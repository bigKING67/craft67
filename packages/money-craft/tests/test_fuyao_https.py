"""Offline HTTPS acceptance of the production urllib opener (synthetic key only)."""
from __future__ import annotations

import http.server
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'skills/money-craft/scripts'))
import money_craft as mc
import fuyao_client


class FuyaoHttpsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which('openssl') is None:
            raise unittest.SkipTest('openssl required for temporary loopback TLS certificate')
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        root = Path(cls.directory.name)
        cert, key = root/'cert.pem', root/'key.pem'
        subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes',
                        '-keyout',str(key),'-out',str(cert),'-days','1',
                        '-subj','/CN=localhost','-addext','subjectAltName=DNS:localhost,IP:127.0.0.1'],
                       check=True, capture_output=True, timeout=15)
        cls.hits = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                # Store paths only, never query parameters containing the synthetic key.
                path = self.path.split('?',1)[0]
                cls.hits.append(path)
                if path.startswith('/shortredirect/'):
                    self.send_response(302)
                    self.send_header('Location','/result')
                    self.send_header('Content-Length','100')
                    self.end_headers()
                    self.wfile.write(b'partial')
                elif path.startswith('/oversized/'):
                    body = b'x'*(fuyao_client.MAX_RESPONSE_BYTES+1)
                    self.send_response(302)
                    self.send_header('Location','/result')
                    self.send_header('Content-Length',str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                elif path.startswith('/same/'):
                    self.send_response(302)
                    self.send_header('Location','/result')
                    self.end_headers()
                elif path.startswith('/downgrade/') or path.startswith('/crosshost/'):
                    self.send_response(302)
                    target = (f'http://127.0.0.1:{cls.server.server_port}/forbidden' if path.startswith('/downgrade/')
                              else f'https://localhost:{cls.server.server_port}/forbidden')
                    self.send_header('Location',target)
                    self.end_headers()
                elif path.startswith('/retry/') or path.startswith('/bad/'):
                    self.send_response(503 if path.startswith('/retry/') else 400)
                    body = b'{"error_message":"fixture error"}'
                    self.send_header('Content-Length',str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    body = b'{"code":0,"message":"ok","request_id":"r","data":{}}'
                    self.send_response(200)
                    self.send_header('Content-Length',str(len(body)+10 if path.startswith('/truncated/') else len(body)))
                    self.end_headers()
                    self.wfile.write(body)

        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.addClassCleanup(cls.server.server_close)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert,key)
        cls.server.socket = context.wrap_socket(cls.server.socket,server_side=True)
        cls.thread = threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.addClassCleanup(cls.stop_server)
        cls.environment = mock.patch.dict(os.environ,{'SSL_CERT_FILE':str(cert),'NO_PROXY':'localhost,127.0.0.1','no_proxy':'localhost,127.0.0.1'})
        cls.environment.start()
        cls.addClassCleanup(cls.environment.stop)

    @classmethod
    def stop_server(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=5)
        if cls.thread.is_alive():
            raise AssertionError('loopback HTTPS fixture did not stop')

    def setUp(self):
        self.hits.clear()

    def client(self, route, sleeps):
        # No opener/SSLContext injection: production build_opener and HTTPSHandler.
        return mc.FuyaoClient('a'*32,base_url=f'https://127.0.0.1:{self.server.server_port}/{route}',sleeper=sleeps.append)

    def test_default_https_opener_accepts_trusted_same_host_redirect(self):
        sleeps = []
        result = self.client('same',sleeps).request('snapshot','/snapshot',{})
        self.assertEqual(result.payload['data'],{})
        self.assertEqual(self.hits,['/same/snapshot','/result'])
        self.assertEqual(sleeps,[])

    def test_default_https_opener_blocks_unsafe_redirect_before_target(self):
        for route in ('downgrade','crosshost'):
            with self.subTest(route=route):
                self.hits.clear()
                sleeps = []
                with self.assertRaises(mc.MoneyCraftError) as caught:
                    self.client(route,sleeps).request('snapshot','/snapshot',{})
                self.assertEqual(caught.exception.kind,'http_error')
                self.assertEqual(self.hits,[f'/{route}/snapshot'])
                self.assertEqual(sleeps,[])

    def test_default_https_opener_bounds_redirect_body(self):
        # Smaller test bound exercises the same production drain without a 10 MiB fixture.
        with mock.patch.object(fuyao_client,'MAX_RESPONSE_BYTES',1024):
            with self.assertRaises(mc.MoneyCraftError) as caught:
                self.client('oversized',[]).request('snapshot','/snapshot',{})
        self.assertEqual(caught.exception.kind,'response_too_large')
        self.assertEqual(self.hits,['/oversized/snapshot'])

    def test_default_https_opener_retries_only_transient_failures(self):
        for route, kind, attempts in (('retry','http_error',3),('truncated','network_error',3),('shortredirect','network_error',3),('bad','http_error',1)):
            with self.subTest(route=route):
                self.hits.clear()
                sleeps = []
                with self.assertRaises(mc.MoneyCraftError) as caught:
                    self.client(route,sleeps).request('snapshot','/snapshot',{})
                self.assertEqual(caught.exception.kind,kind)
                self.assertEqual(len(self.hits),attempts)
                self.assertEqual(sleeps,[0.5,1.0] if attempts == 3 else [])
