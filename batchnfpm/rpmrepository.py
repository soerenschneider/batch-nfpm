import repomd

class RpmRepository:
    def __init__(self, rpm_repo):
        if not rpm_repo:
            raise ValueError("No repo given")
        self._load_repo(rpm_repo)

    def _load_repo(self, rpm_repo: str):
        self.rpm_repo = repomd.load(rpm_repo)

    def get_rpm_version(self, name: str) -> str:
        package = self.rpm_repo.find(name)
        if not package:
            return None

        return package.version