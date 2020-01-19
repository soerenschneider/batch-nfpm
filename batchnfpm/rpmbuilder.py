import os
import subprocess
import logging
import configargparse

from packaging.version import Version

from batchnfpm.gitwrapper import GitWrapper
from batchnfpm.rpmrepository import RpmRepository
from batchnfpm.config import BuildConfig, NfpmConfig, Config

NFPM_VERSION_ENV_VAR = "NFPM_APP_VERSION"


class PackageBuilder:
    def __init__(self, conf: Config, git_wrapper: GitWrapper, rpm_repo=None):
        if not conf:
            raise ValueError("No config provided")
        self.conf = conf

        if not git_wrapper:
            raise ValueError("No git_wrapper defined")
        self.git_wrapper = git_wrapper

        if not rpm_repo:
            logging.info("No remote package repository defined")
        else:
            logging.info("Using '%s' as remote package repository", rpm_repo)
        self.rpm_repo = rpm_repo

    def _find_nfpm_config(self, nfpm_config: NfpmConfig, build_config: BuildConfig) -> str:
        owner = build_config.owner
        project = build_config.project
        path = nfpm_config.local_path

        if nfpm_config.fetch_resource:
            GitWrapper.checkout(nfpm_config.fetch_resource, nfpm_config.local_path)
        
        # TODO: enable individual overwriting
        return os.path.join(path, build_config.host, owner, project, build_config.config_file)

    @staticmethod
    def _compile_project(build_config: BuildConfig, working_dir: str) -> bool:
        try:
            for cmd in build_config.get_cmds():
                logging.info("Executing build command '%s'", cmd)
                p = subprocess.Popen(cmd, cwd=working_dir)
                p.wait()
        except Exception as err:
            logging.error("Could not build repo: %s", err)
            return False

        return True

    def _compile_and_package(self, working_dir: str, build_config: BuildConfig, version: str) -> bool:
        nfpm_config = self._find_nfpm_config(self.conf.nfpm_config, build_config)
        if not nfpm_config or not os.path.isfile(nfpm_config):
            logging.error(f"No nfpm file '%s' defined for %s/%s", nfpm_config, build_config.owner, build_config.project)
            return False

        build_success = PackageBuilder._compile_project(build_config, working_dir)
        if not build_success:
            return False

        version = PackageBuilder._get_normalized_version(version)
        self._build_package(build_config, nfpm_config, version, working_dir)
        
        return True

    def _build_package(self, build_config: BuildConfig, nfpm_config: str, version: str, working_dir):
        for package_format in build_config.get_formats():
            package_path = self._get_package_file_path(build_config, version, package_format)

            # dynamically set the version
            os.environ[NFPM_VERSION_ENV_VAR] = version
            os.environ["MY_APP_VERSION"] = version
            
            package_cmd = ["nfpm", "-f", nfpm_config, "pkg", "-t", package_path]
            p = subprocess.Popen(package_cmd, cwd=working_dir)
            p.wait()

    @staticmethod
    def _get_target_filename(project: str, package_type: str, version=None) -> str:
        if not version:
            version = ""
        else:
            version = f"-{version}"
            
        if not package_type:
            package_type = "rpm"

        return f"{project}{version}.{package_type}"

    def _get_package_file_path(self, build_config: BuildConfig, version: str, package_format: str) -> str:
        if not build_config or not package_format:
            raise ValueError("no build_config and/or package_format supplied")

        package_path = os.path.join(self.conf.artifacts_path, package_format)
        if not os.path.isdir(package_path):
            logging.info("Creating non-existing directory %s", package_path)
            os.mkdir(package_path)

        package_filename = PackageBuilder._get_target_filename(build_config.project, package_format, version)
        return os.path.join(package_path, package_filename)

    @staticmethod
    def _get_normalized_version(version: str) -> str: 
        if version and version.lower().startswith("v"):
            return version[1:]
        
        return version

    @staticmethod
    def _is_git_tag_newer(git_tag: str, package_version: str):
        if not package_version:
            logging.info("No package version from package repo available")
            return True

        logging.info("Comparing versions from git (%s) and package from repository (%s)", git_tag, package_version)
        return Version(git_tag) > Version(package_version)

    def _get_packaged_version(self, build_config: BuildConfig):
        if self.rpm_repo:
            return self.rpm_repo.get_rpm_version(build_config.owner)
        return None

    def build_packages(self):
        for build_config in self.conf.buildconfigs:
            logging.info("Checking build %s", build_config)
            git_tag = GitWrapper.get_latest_release_tag(build_config)
            if not git_tag:
                logging.warning("No release found for %s/%s", build_config.owner, build_config.project)
            else:
                package_version = self._get_packaged_version(build_config)
                
                if self.conf.force or self._is_git_tag_newer(git_tag, package_version):
                    logging.info("Building package from git tag %s", git_tag)
                    working_dir = self.git_wrapper.checkout_build_config(build_config, git_tag)
                    self._compile_and_package(working_dir, build_config, version=git_tag)
                else:
                    logging.info("Not building package for git tag %s", git_tag)
