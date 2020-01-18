import logging
import os

from enum import Enum

builds_node = "builds"
DEFAULT_CONFIG_NAME = "nfpm.yaml"


class Hoster(Enum):
    GITHUB = "GITHUB"
    GITLAB = "GITLAB"


class Config:
    def __init__(self, buildconfigs: list, artifacts_path: str, clone_path: str, nfpm_config: str, dnf_repository=None):
        if not buildconfigs or len(buildconfigs) < 1:
            raise ValueError("no buildconfig supplied")
        self.buildconfigs = buildconfigs

        if not artifacts_path:
            raise ValueError("no artifacts_path defined")
        self.artifacts_path = artifacts_path

        if not clone_path:
            raise ValueError("no clone_path defined")
        self.clone_path = clone_path

        if not nfpm_config:
            raise ValueError("no nfpm_config defined")
        self.nfpm_config = nfpm_config

        self.dnf_repository = dnf_repository
        self.force = False

    def __repr__(self):
        return f"artifacts_path: {self.artifacts_path}, clone_path: {self.clone_path}, repo: {self.dnf_repository}, force: {self.force}"

    @staticmethod
    def from_json(raw):
        if not raw or builds_node not in raw:
            raise ValueError("Can not read config")

        buildconfigs = []
        for entry in raw[builds_node]["build_configurations"]:
            build_conf = BuildConfig.as_payload(entry)
            buildconfigs.append(build_conf)

        artifacts_path = None
        if "artifacts_path" in raw[builds_node]:
            artifacts_path = raw[builds_node]["artifacts_path"]

        clone_path = None
        if "clone_path" in raw[builds_node]:
            clone_path = raw[builds_node]["clone_path"]

        dnf_repo = None
        if "dnf_repository" in raw[builds_node]:
            repo_path = raw[builds_node]["dnf_repository"]

        nfpm_config = None
        if "nfpm_config" in raw[builds_node]:
            nfpm_config = NfpmConfig.from_json(raw[builds_node]['nfpm_config'])

        return Config(buildconfigs, artifacts_path=artifacts_path, clone_path=clone_path, nfpm_config=nfpm_config, dnf_repository=dnf_repo)


class NfpmConfig:
    def __init__(self, local_path: str, fetch_resource=None):
        if not local_path:
            raise ValueError("local_path not set")
        self.local_path = local_path

        self.fetch_resource = fetch_resource

    def __repr__(self):
        return f"{self.local_path}, {self.fetch_resource}"

    @staticmethod
    def from_json(raw):
        fetch_resource = None
        if "fetch_resource" in raw:
            fetch_resource = raw["fetch_resource"]

        local_path = None
        if "local_path" in raw:
            local_path = raw["local_path"]
        else:
            # if simple yaml value instead of object
            local_path = raw

        conf = NfpmConfig(local_path, fetch_resource)
        return conf


class BuildConfig:
    def __init__(self, commands: list, owner: str, project: str, hoster=None):
        if not commands:
            raise ValueError("commands empty")
        self.commands = commands

        if not hoster:
            hoster = Hoster.GITHUB
        elif not isinstance(hoster, Hoster):
            hoster = Hoster(hoster.upper())
        self.hoster = hoster

        if not owner:
            raise ValueError("owner empty")
        self.owner = owner        

        if not project:
            raise ValueError("project empty")
        self.project = project

        # TODO: make them available in config
        self.formats = None
        # TODO: make avaiable in config
        self._config_file = DEFAULT_CONFIG_NAME

    def get_formats(self):
        if not self.formats:
            # by default, only build RPM packages
            return ["rpm"]

        return self.formats

    @property
    def config_file(self):
        if not self._config_file:
            return DEFAULT_CONFIG_NAME

        return self._config_file

    @config_file.setter
    def config_file(self, v):
        self._config_file = v

    @property
    def host(self):
        if Hoster.GITHUB == self.hoster:
            return "github.com"
        if Hoster.GITLAB == self.hoster:
            return "gitlab.com"
        return None

    def __repr__(self):
        return f"{self.hoster}: {self.owner}/{self.project}, commands: {self.commands}"

    def get_cmds(self) -> list:
        commands = []
        
        for cmd in self.commands:
            commands.append(cmd.split())

        return commands

    def get_repository_url(self) -> str:
        if Hoster.GITHUB == self.hoster:
            return f"https://github.com/{self.owner}/{self.project}.git"
        
        return f"https://gitlab.com/{self.owner}/{self.project}.git"

    @staticmethod
    def as_payload(payload):
        return BuildConfig(
            payload['commands'], 
            payload['owner'],
            payload['project'],
            
            hoster=payload['hoster'], 
        )
