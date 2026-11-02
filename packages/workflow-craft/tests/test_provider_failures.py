"""Provider failures stay structured through real HTTP reads and the public CLI."""
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from test_workflow import Fixture, RUNTIME
from twc_lib.providers import CNB, Gitea, ProviderError


# Route only the test process's HTTPS transport to a real loopback HTTP socket.
# Policy, adapters, response reads, task handling and CLI error paths stay real.
CLI_TRANSPORT = '''import sys, http.client, urllib.request
from unittest.mock import patch
sys.path.insert(0, sys.argv.pop(1))
port = int(sys.argv.pop(1))
class LocalHTTPS(urllib.request.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(lambda *args, **kwargs:
            http.client.HTTPConnection("127.0.0.1", port, timeout=3), req)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), LocalHTTPS())
import twc
with patch("twc_lib.providers.http.request.build_opener", return_value=opener):
    raise SystemExit(twc.main())
'''


class _ProviderHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        path = self.path.split('?')[0]
        cls = type(self)
        cls.paths.append(path)
        if path.endswith('/user') and cls.truncated_reads:
            cls.truncated_reads -= 1
            body = b'{"private-marker": 1}'
            self.send_response(200)
            self.send_header('Transfer-Encoding', 'chunked')
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(f'{len(body):x}\r\n'.encode() + body + b'\r\n')
            self.wfile.flush()
            self.close_connection = True  # Deliberately omit the final zero chunk.
            return
        if '/pulls/3' in path and not path.endswith('/reviews'):
            payload = dict(number=3 if cls.provider == 'gitea' else '3', **cls.references)
        elif path.endswith('/reviews') or '/statuses/' in path or 'commit-statuses/' in path:
            payload = []
        elif path.endswith('/user'):
            payload = dict(id=1 if cls.provider == 'gitea' else '1', login='fixture-user',
                           username='fixture-user', full_name='Fixture')
        elif path.endswith('/version'):
            payload = dict(version='fixture')
        else:
            payload = dict(full_name='team/product', default_branch='main',
                           path='team/product', visibility_level='private')
        body = json.dumps(payload).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class GiteaFailureTests(Fixture):
    provider = 'gitea'

    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), _ProviderHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        super().setUp()
        if self.provider == 'cnb':
            self.use_cnb()
        _ProviderHandler.provider = self.provider
        _ProviderHandler.paths = []
        _ProviderHandler.truncated_reads = 0
        self.references = dict(head=dict(sha=self.git('rev-parse', 'HEAD')), base=dict(sha=self.base))
        _ProviderHandler.references = self.references
        env = patch.dict(os.environ, TWC_GITEA_TOKEN='fixture-only-token',
                         TWC_CNB_TOKEN='fixture-only-token', TWC_CNB_IDENTITY_TOKEN='fixture-only-token')
        env.start()
        self.addCleanup(env.stop)

    def api(self):
        factory = Gitea if self.provider == 'gitea' else CNB
        return factory(f'http://127.0.0.1:{self.server.server_port}', 'team/product',
                       allow_loopback_http=True, retry_delay=0, timeout=3)

    def cli(self, *args, expected=0):
        result = subprocess.run([sys.executable, '-B', '-c', CLI_TRANSPORT, str(RUNTIME),
                                 str(self.server.server_port), '--project', str(self.root), *args],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, expected, result.stderr or result.stdout)
        self.assertEqual(result.stderr, '')
        self.assertNotIn('fixture-only-token', result.stdout)
        self.assertNotIn('private-marker', result.stdout)
        return json.loads(result.stdout)

    def test_change_reference_shapes_are_validated_at_the_provider_boundary(self):
        for field in ('head', 'base'):
            for value in ('private-marker', ['private-marker'], 0, False,
                          {'sha': ''}, {'sha': 1}, {'sha': True},
                          {'sha': ['private-marker']}, {'sha': {'private-marker': 1}}):
                with self.subTest(field=field, value=value):
                    _ProviderHandler.references = dict(self.references, **{field: value})
                    with self.assertRaises(ProviderError) as caught:
                        self.api().get_change(3)
                    self.assertEqual(caught.exception.code, 'invalid_response')
                    self.assertNotIn('private-marker', str(caught.exception))

    def test_missing_change_references_remain_unknown_and_raw_valid_fields_survive(self):
        for refs in ({}, dict(head=None, base=None), dict(head={}, base={}), self.references):
            with self.subTest(refs=refs):
                _ProviderHandler.references = refs
                expected = dict(number=3 if self.provider == 'gitea' else '3', **refs)
                self.assertEqual(self.api().get_change(3), expected)
        _ProviderHandler.references = dict(head=None, base=None)
        result = self.cli('prepare', '--task', 'pr:3', '--contract', 'contract.json')
        packet = json.loads((self.root / result['packet']).read_text(encoding='utf-8'))
        self.assertEqual(packet['platform']['checks']['status'], 'unknown')

    def test_prepare_reports_invalid_pr_head_without_a_traceback(self):
        _ProviderHandler.references = dict(self.references, head='private-marker')
        result = self.cli('prepare', '--task', 'pr:3', '--contract', 'contract.json')
        self.assertEqual(result['platform_status'], 'invalid_response')
        packet = json.loads((self.root / result['packet']).read_text(encoding='utf-8'))
        self.assertEqual(packet['platform']['checks']['status'], 'unknown')
        self.assertIsNone(packet['platform']['change']['data'])

    def test_handoff_reports_invalid_pr_base_without_advisory_readiness(self):
        self.prepare()
        self.verify()
        _ProviderHandler.references = dict(self.references, base='private-marker')
        result = self.cli('handoff', '--draft', '--online', '--done', 'implemented feature',
                          '--next', 'review the feature')
        self.assertEqual(result['platform']['status'], 'invalid_response')
        self.assertIn('platform_not_current', result['unknowns'])
        self.assertNotEqual(result['readiness'], 'advisory_ready')

    def test_truncated_chunk_retries_are_bounded_and_doctor_stays_structured(self):
        _ProviderHandler.truncated_reads = 100
        result = self.cli('doctor', '--online', expected=1)
        self.assertEqual(result['status'], 'attention_required')
        self.assertEqual(result['platform']['identity']['status'], 'unavailable')
        self.assertEqual(sum(path.endswith('/user') for path in _ProviderHandler.paths), 3)

    def test_transient_chunk_truncation_retries_and_recovers(self):
        _ProviderHandler.truncated_reads = 1
        result = self.cli('doctor', '--online')
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['platform']['identity']['status'], 'observed')
        self.assertEqual(sum(path.endswith('/user') for path in _ProviderHandler.paths), 2)


class CNBFailureTests(GiteaFailureTests):
    provider = 'cnb'
