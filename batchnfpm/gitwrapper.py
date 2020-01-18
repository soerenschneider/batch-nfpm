import os
import logging

import requests
from git import Git, Repo

from batchnfpm.config import Config, Hoster, BuildConfig


class GitWrapper:
    def __init__(self, path):
        if not path:
            raise ValueError("path must be set")

        self.path = path

    def get_local_repo_path(self, owner: str, project: str) -> str:
        added_path = f"{owner}/{project}"
        return os.path.join(self.path, added_path)

    def checkout_build_config(self, build_config: BuildConfig, tag=None):
        repo_url = build_config.get_repository_url()
        local_repo_path = self.get_local_repo_path(build_config.owner, build_config.project)

        return GitWrapper.checkout(repo_url, local_repo_path, tag)

    @staticmethod
    def checkout(repository_url: str, local_repo_path: str, tag=None) -> str:
        if not repository_url or not local_repo_path:
            raise ValueError("no repository/local_repo_path given")

        if not tag:
            tag = "master"

        if os.path.isdir(local_repo_path):
            logging.info("Checking out tag %s for %s", tag, repository_url)
            g = Git(local_repo_path)
            g.checkout(tag)
        else:
            logging.info("Cloning '%s' with tag '%s' to %s", repository_url, tag, local_repo_path)
            Repo.clone_from(repository_url, local_repo_path, branch=tag)

        return local_repo_path

    @staticmethod
    def get_latest_release_tag(repo):
        if not repo:
            return None

        if Hoster.GITHUB == repo.hoster:
            return GitWrapper._get_github_tag(repo.owner, repo.project)
        
        elif Hoster.GITLAB == repo.hoster:
            return GitWrapper._get_gitlab_tag(repo.owner, repo.project)

        return None

    @staticmethod
    def _get_github_tag(owner: str, project: str) -> str:
        url = f"https://api.github.com/repos/{owner}/{project}/releases/latest"
        response = requests.get(url)
        if response.ok:
            data = response.json()
            if 'tag_name' in data:
                return data['tag_name']

        return None

    @staticmethod
    def _get_gitlab_tag(owner: str, project: str, host="gitlab.com") -> str:
        project_id = GitWrapper._get_gitlab_project_id(owner, project, host)
        if not project_id:
            return 

        url = f"https://{host}/api/v4/projects/{project_id}/releases"
        response = requests.get(url)
        if not response.ok:
            return None

        releases = response.json()
        if releases and len(releases) > 0:
            return releases[0]["tag_name"]

        return None

    @staticmethod
    def _get_gitlab_project_id(owner: str, project: str, host: str) -> int:
        url = f"https://{host}/api/v4/projects/{owner}%2F{project}"
        response = requests.get(url)
        if not response.ok:
            return None
        return response.json()["id"]
