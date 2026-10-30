"""CNB OpenAPI contracts against a local HTTP fixture; no company credentials."""
import os
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from test_gitea import _GiteaHandler, _FailingOpener
from twc_lib.providers import CNB, ProviderError
from twc_lib import context, actors


class CNBAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), _GiteaHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        _GiteaHandler.routes = {}
        _GiteaHandler.requests = []
        self.env = patch.dict(os.environ, TWC_CNB_FIXTURE_TOKEN='fixture-token')
        self.env.start()
        self.addCleanup(self.env.stop)

    def api(self, **options):
        return CNB(self.url, 'org/sub/repo', 'TWC_CNB_FIXTURE_TOKEN',
                   allow_loopback_http=True, retry_delay=0, **options)

    def route(self, path, payload, query=None, status=200, headers=None):
        _GiteaHandler.routes[(path, tuple(sorted((query or {}).items())))] = (status, payload, headers or {})

    def test_native_paths_auth_and_identity_mapping(self):
        self.route('/user', dict(id='18446744073709551616', username='sixseven', nickname='成员',
                                 email='private@invalid', identity_providers={'secret': 'never-save'}))
        self.route('/org/sub/repo', dict(path='org/sub/repo', visibility_level='private'))
        self.route('/org/sub/repo/-/issues/3', dict(number='3', assignees=[{'username': 'alice'}]))
        self.route('/org/sub/repo/-/pulls/4', dict(number='4', head={'sha': 'a' * 40}))
        api = self.api()
        identity = api.get_identity()
        self.assertEqual(identity, dict(id='18446744073709551616', login='sixseven', full_name='成员'))
        self.assertIsNotNone(actors.account(identity, 'cnb'))
        self.assertIsNone(actors.account(identity, 'gitea'))
        self.assertEqual(api.get_repository()['path'], 'org/sub/repo')
        self.assertEqual(api.get_task(3)['assignees'], [{'username': 'alice'}])
        self.assertEqual(api.get_change(4)['number'], '4')
        self.assertTrue(all(header == 'Bearer fixture-token' for _, header in _GiteaHandler.requests))
        self.assertFalse(any('/api/v1' in path for path, _ in _GiteaHandler.requests))

    def test_review_pagination_uses_page_size_and_does_not_trust_short_pages(self):
        for page, data in [(1, [{'id': 'r1'}]), (2, [{'id': 'r2'}]), (3, [])]:
            self.route('/org/sub/repo/-/pulls/4/reviews', data,
                       {'page': (str(page),), 'page_size': ('50',)})
        self.assertEqual(self.api().get_reviews(4), [{'id': 'r1'}, {'id': 'r2'}])
        with self.assertRaises(ProviderError) as caught:
            self.api(max_pages=2).get_reviews(4)
        self.assertEqual(caught.exception.code, 'incomplete')

    def test_checks_are_exact_sha_unpaginated_and_empty_is_not_a_pass(self):
        sha = 'b' * 40
        self.route('/org/sub/repo/-/git/commit-statuses/' + sha, [])
        self.assertEqual(self.api().get_checks(sha), [])
        self.assertNotIn('?', _GiteaHandler.requests[-1][0])
        for ref in ['main', 'abc', 'a' * 39, '../main', True]:
            with self.subTest(ref=ref), self.assertRaises(ProviderError):
                self.api().get_checks(ref)

    def test_resource_number_is_checked_without_coercion(self):
        for number in ['5', '04', 4.0, True, None]:
            self.route('/org/sub/repo/-/issues/4', {'number': number})
            with self.subTest(number=number), self.assertRaises(ProviderError):
                self.api().get_task(4)

    def test_cnb_rejects_other_origins_and_unsafe_paths(self):
        for url in ['https://api.cnb.cool', 'https://cnb.cool/other', 'https://evil.invalid',
                    'http://cnb.cool', 'https://token@cnb.cool', 'https://cnb.cool?token=x']:
            with self.subTest(url=url), self.assertRaises(ProviderError):
                CNB(url, 'org/repo')
        for repo in ['repo', 'org/../repo', 'org//repo', 'org/r%2Fsecret', 'org/repo.git']:
            with self.subTest(repo=repo), self.assertRaises(ProviderError):
                CNB('https://cnb.cool', repo)
        api = CNB('https://cnb.cool/', 'org/sub/repo')
        self.assertEqual(api._base_url, 'https://api.cnb.cool')

    def test_missing_auth_denials_redirects_and_network_errors_remain_safe(self):
        with patch.dict(os.environ, TWC_CNB_FIXTURE_TOKEN=''):
            with self.assertRaises(ProviderError) as caught:
                self.api().get_identity()
            self.assertEqual(caught.exception.code, 'auth_required')
        self.assertEqual(_GiteaHandler.requests, [])
        for status, code in [(401, 'auth_required'), (403, 'forbidden'), (404, 'not_found'), (302, 'unavailable')]:
            self.route('/user', {'message': 'fixture-token'}, status=status, headers={'Location': 'https://evil.invalid'})
            with self.subTest(status=status), self.assertRaises(ProviderError) as caught:
                self.api(retries=0).get_identity()
            self.assertEqual(caught.exception.code, code)
            self.assertNotIn('fixture-token', str(caught.exception))
        opener = _FailingOpener()
        with self.assertRaises(ProviderError):
            self.api(opener=opener, retries=1).get_identity()
        self.assertEqual(opener.calls, 2)

    def test_invalid_payloads_and_version_are_not_fabricated(self):
        for payload in [b'bad JSON', [], None]:
            self.route('/user', payload)
            with self.subTest(payload=payload), self.assertRaises(ProviderError):
                self.api().get_identity()
        self.route('/org/sub/repo/-/git/commit-statuses/' + 'a' * 40, {'state': 'success'})
        with self.assertRaises(ProviderError):
            self.api().get_checks('a' * 40)
        before = len(_GiteaHandler.requests)
        with self.assertRaises(ProviderError) as caught:
            self.api().get_version()
        self.assertEqual(caught.exception.code, 'unsupported')
        self.assertEqual(len(_GiteaHandler.requests), before)

    def test_pr_snapshot_never_reads_an_issue_with_same_number(self):
        self.route('/org/sub/repo/-/pulls/3', {'number': '3', 'head': {'sha': 'c' * 40}})
        self.route('/org/sub/repo/-/pulls/3/reviews', [], {'page': ('1',), 'page_size': ('50',)})
        self.route('/org/sub/repo/-/git/commit-statuses/' + 'c' * 40, [])
        with patch.object(context, 'provider', return_value=self.api()):
            snapshot = context.platform_snapshot({}, {'type': 'pr', 'number': 3})
        self.assertEqual(snapshot['status'], 'observed')
        self.assertEqual(snapshot['change']['data']['number'], '3')
        self.assertEqual(snapshot['checks']['data'], [])
        self.assertIn('merge-preview', snapshot['checks_coverage'])
        self.assertFalse(any('/issues/' in path for path, _ in _GiteaHandler.requests))

    def test_separate_identity_token_does_not_broaden_or_replace_repository_credential(self):
        self.route('/user', {'id': '123', 'username': 'sixseven'})
        self.route('/org/sub/repo', {'path': 'org/sub/repo'})
        with patch.dict(os.environ, TWC_IDENTITY_FIXTURE='identity-only'):
            api = self.api(identity_token_env='TWC_IDENTITY_FIXTURE')
            self.assertEqual(api.get_identity()['login'], 'sixseven')
            self.assertEqual(api.get_repository()['path'], 'org/sub/repo')
        self.assertEqual(_GiteaHandler.requests,
                         [('/user', 'Bearer identity-only'), ('/org/sub/repo', 'Bearer fixture-token')])

    def test_missing_identity_credential_never_falls_back_to_repository_token(self):
        self.route('/org/sub/repo', {'path': 'org/sub/repo'})
        with patch.dict(os.environ, TWC_IDENTITY_FIXTURE=''):
            api = self.api(identity_token_env='TWC_IDENTITY_FIXTURE')
            with self.assertRaises(ProviderError) as caught:
                api.get_identity()
            self.assertEqual(caught.exception.code, 'auth_required')
            self.assertEqual(_GiteaHandler.requests, [])
            self.assertEqual(api.get_repository()['path'], 'org/sub/repo')
