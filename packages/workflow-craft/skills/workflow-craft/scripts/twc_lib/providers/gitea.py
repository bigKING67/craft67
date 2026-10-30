"""Read-only Gitea API v1; commit statuses do not prove all merge gates."""
from typing import Any, Mapping

from .http import ReadOnlyAPI, ProviderError


class Gitea(ReadOnlyAPI):
    api_prefix = "/api/v1"
    auth_scheme = "token"
    page_size_parameter = "limit"

    def __init__(self, base_url, repository, token_env="TWC_GITEA_TOKEN", timeout=10, **options):
        self._owner, self._repo = self._validate_repository(repository)
        super().__init__(base_url, token_env, timeout, **options)

    def get_identity(self) -> dict[str, Any]:
        return self._object("/user")


    def get_repository(self) -> dict[str, Any]:
        return self._object(self._repo_path())


    def get_version(self) -> dict[str, Any]:
        return self._object("/version")


    def get_task(self, number: int) -> dict[str, Any]:
        data = self._object(f"{self._repo_path()}/issues/{self._number(number)}")
        self._require_matching_number(data, number)
        return data


    def get_change(self, number: int) -> dict[str, Any]:
        data = self._object(f"{self._repo_path()}/pulls/{self._number(number)}")
        self._require_matching_number(data, number)
        return data


    def get_reviews(self, number: int) -> list[Any]:
        return self._list(f"{self._repo_path()}/pulls/{self._number(number)}/reviews")


    def get_checks(self, sha: str) -> list[Any]:
        """Return raw commit-status rows for ``sha``.

        The Gitea statuses endpoint does not prove that every Actions job or
        provider-specific check ran.  Callers must represent unavailable or
        unknown evidence as such; an empty list is never synthesized into a
        passing result.
        """

        return self._list(f"{self._repo_path()}/statuses/{self._sha(sha)}")


    @staticmethod
    def _validate_repository(repository: str) -> tuple[str, str]:
        if not isinstance(repository, str) or repository.count("/") != 1:
            raise ProviderError("invalid_response", "repository must have the form owner/name")
        owner, repo = repository.split("/", 1)
        for segment in (owner, repo):
            if (
                not segment
                or segment in {".", ".."}
                or any(character in segment for character in "\\?#%")
                or any(character.isspace() for character in segment)
                or any(ord(character) < 32 for character in segment)
            ):
                raise ProviderError("invalid_response", "repository must have safe owner and name segments")
        return owner, repo


    def _repo_path(self) -> str:
        return "/repos/{}/{}".format(self._segment(self._owner), self._segment(self._repo))


    @staticmethod
    def _require_matching_number(data: Mapping[str, Any], expected: int) -> None:
        actual = data.get("number")
        if isinstance(actual, bool) or not isinstance(actual, int) or actual != expected:
            raise ProviderError("invalid_response", "Gitea returned a resource with a mismatched number")


