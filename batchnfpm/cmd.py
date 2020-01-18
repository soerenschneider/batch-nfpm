import logging
import subprocess
import sys

import configargparse
from batchnfpm.config import Config
from batchnfpm.rpmbuilder import GitWrapper, PackageBuilder
from batchnfpm.rpmrepository import RpmRepository
from batchnfpm.resources import ResourceReader, DEFAULT_LOCATIONS

def parse_args():
    parser = configargparse.ArgumentParser(prog="batchnfpm")
    parser.add_argument(
        "-f",
        "--force",
        dest="force",
        env_var="NFPM_FORCE",
        action="store_true",
        help="Force building a new package even though the identical version was found in the remote package repository",
        default=None,
    )
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        env_var="NFPM_CONFIG",
        action="store",
        help=f"Read the config from a given resource instead of its default locations ({DEFAULT_LOCATIONS})",
        default=None
    )
    parser.add_argument(
        "--artficats-path",
        dest="artifacts_path",
        env_var="NFPM_ARTIFACTS_PATH",
        action="store",
        help="Overwrite the config's artifact_path variable. Denotes where to store all build artifacts.",
        default=None
    )
    parser.add_argument(
        "--clone-path",
        dest="clone_path",
        env_var="NFPM_CLONE_PATH",
        action="store",
        help="Overwrite the config's clone_path variable. Denotes where all the build repositories are checked out to.",
        default=None
    )
    parser.add_argument(
        "--package-repository",
        dest="package_repo",
        env_var="NFPM_PACKAGE_REPOSITORY",
        action="store",
        help="Overwrite the config's package_repo variable. Defines a remote package repository (RPM/DEB) to fetch and compare package information.",
        default=None
    )
    parser.add_argument(
        "-v"
        "--verbose",
        dest="verbose",
        env_var="NFPM_VERBOSE",
        action="store_true",
        help="Log with debug output",
        default=False
    )

    return parser.parse_args()


def _setup_logging(debug=False):
    """ Sets up the logging. """
    loglevel = logging.INFO
    if debug:
        loglevel = logging.DEBUG
    logging.basicConfig(
        level=loglevel, format="%(levelname)s\t %(asctime)s %(message)s"
    )

def _check_precondition() -> bool:
    try:
        package_cmd = ["nfpm", "--help"]
        p = subprocess.Popen(package_cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        p.wait()
    except Exception as err:
        logging.error("Checking preconditions failed: %s", err)
        return False
    return True

def _overwrite_config(args: configargparse.Namespace, config: Config):
    if not args or not config:
        raise ValueError("args and/or config not set")

    if args.package_repo:
        config.dnf_repository = args.package_repo

    if args.clone_path:
        config.clone_path = args.clone_path

    if args.artifacts_path:
        config.artifacts_path = args.artifacts_path

    if args.force is not None:
        config.force = args.force

def _build_config(args) -> Config:
    config_string = ResourceReader.read_config(args.config)
    if not config_string:
        logging.error("Could not find a config file")
        sys.exit(1)

    try:
        config = Config.from_json(config_string)
    except ValueError as err:
        logging.error("Can not parse config: %s", err)

    if not config:
        logging.error("Could not read valid config")
        sys.exit(1)

    return config

def main():
    args = parse_args()
    _setup_logging(args.verbose)

    if not _check_precondition():
        sys.exit(1)

    config = _build_config(args)
    _overwrite_config(args, config)
    git_wrapper = GitWrapper(config.clone_path)

    rpm_repo = None
    if config.dnf_repository:
        rpm_repo = RpmRepository(config.dnf_repository)

    builder = PackageBuilder(config, git_wrapper, rpm_repo)
    builder.build_packages()