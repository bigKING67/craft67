"""CNB public OpenAPI: read-only facts, not a Gitea-compatible API.

Uses the schema published at https://api.cnb.cool/swagger.json. Native issue,
PR and review fields are preserved; only operator identity is normalized.
"""
import re
from urllib.parse import urlsplit

from .http import ReadOnlyAPI, ProviderError


class CNB(ReadOnlyAPI):
    accept = "application/vnd.cnb.api+json"

    def __init__(self, base_url, repository, token_env="TWC_CNB_TOKEN", timeout=10,
                 *, identity_token_env=None, **options):
        super().__init__(base_url, token_env, timeout, **options)
        # CNB SaaS has distinct web and API origins. Never send its token to an
        # arbitrary derived hostname. A loopback endpoint is only for tests.
        local = options.get('allow_loopback_http') and self._is_loopback(urlsplit(self._base_url).hostname)
        if self._base_url != 'https://cnb.cool' and not local:
            raise ProviderError('invalid_response', 'CNB base URL must be https://cnb.cool')
        if not isinstance(repository, str):
            raise ProviderError('invalid_response', 'CNB repository path is invalid')
        segments = repository.split('/')
        if (len(segments) < 2 or repository.endswith('.git')
                or any(not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]*', s)
                       or s in ('.', '..') for s in segments)):
            raise ProviderError('invalid_response', 'CNB repository requires safe organization/repository segments')
        self._repository = '/'.join(self._segment(s) for s in segments)
        if not local:
            self._base_url = 'https://api.cnb.cool'
        # A repo-scoped CNB token cannot retain account-profile permission.
        # Keep account reads separate instead of broadening repository access.
        self._identity_api = None
        if identity_token_env is not None:
            self._identity_api = ReadOnlyAPI(self._base_url, identity_token_env, timeout, **options)
            self._identity_api.accept = self.accept

    def _repo_path(self):
        return '/' + self._repository

    def get_identity(self):
        user = (self._identity_api or self)._object('/user')
        # Do not propagate email, linked identity providers or other profile data.
        return dict(id=user.get('id'), login=user.get('username'), full_name=user.get('nickname'))

    def get_repository(self):
        return self._object(self._repo_path())

    def get_version(self):
        raise ProviderError('unsupported', 'CNB SaaS does not expose a server version endpoint')

    def _numbered(self, kind, number):
        data = self._object(f'{self._repo_path()}/-/{kind}/{self._number(number)}')
        # CNB OpenAPI represents these numbers as strings; accept an exact
        # positive integer too, without accepting bools, floats or coercions.
        actual = data.get('number')
        if not ((type(actual) is int and actual == number)
                or (isinstance(actual, str) and actual == str(number))):
            raise ProviderError('invalid_response', 'CNB returned a mismatched resource number')
        return data

    def get_task(self, number):
        return self._numbered('issues', number)

    def get_change(self, number):
        return self._numbered('pulls', number)

    def get_reviews(self, number):
        return self._list(f'{self._repo_path()}/-/pulls/{self._number(number)}/reviews')

    def get_checks(self, sha):
        # This endpoint is not paginated. It describes one exact commit, not
        # every PR policy or the current merge-preview result.
        if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-fA-F]{40}|[0-9a-fA-F]{64}', sha):
            raise ProviderError('invalid_response', 'CNB checks require a full commit SHA')
        data = self._get(f'{self._repo_path()}/-/git/commit-statuses/{sha}').data
        if not isinstance(data, list):
            raise ProviderError('invalid_response', 'CNB returned an unexpected status list')
        return data
