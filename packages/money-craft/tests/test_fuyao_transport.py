from __future__ import annotations
import io
import sys
from pathlib import Path
import unittest
import urllib.error
import urllib.request
from test_provider import FakeOpener, FakeResponse, response
import money_craft as mc
import fuyao_client

class FuyaoTransportTests(unittest.TestCase):
    def test_redirect_rejects_https_downgrade(self):
        request=urllib.request.Request('https://fixture.invalid/data')
        with self.assertRaises(urllib.error.HTTPError) as caught:
            fuyao_client.SameHostRedirectHandler().redirect_request(request,None,302,'redirect',{},'http://fixture.invalid/data')
        caught.exception.close()

    def test_http_error_body_is_closed(self):
        for status in (400,429,503):
            with self.subTest(status=status):
                bodies=[io.BytesIO(b'synthetic body') for _ in range(3 if status!=400 else 1)]
                errors=[urllib.error.HTTPError('https://fixture.invalid',status,'failure',{},body) for body in bodies]
                with self.assertRaises(mc.MoneyCraftError):
                    mc.FuyaoClient('synthetic',opener=FakeOpener(errors),sleeper=lambda _:None).request('snapshot','/snapshot',{})
                self.assertTrue(all(body.closed for body in bodies))

    def test_short_success_body_is_retried(self):
        raw=b'{"code":0,"message":"ok","request_id":"r","data":{}}'
        opener=FakeOpener([FakeResponse(raw,{'Content-Length':str(len(raw)+1)}) for _ in range(3)])
        with self.assertRaises(mc.MoneyCraftError) as caught:
            mc.FuyaoClient('synthetic',opener=opener,sleeper=lambda _:None).request('snapshot','/snapshot',{})
        self.assertEqual(caught.exception.kind,'network_error')
        self.assertEqual(len(opener.requests),3)

    def test_json_numeric_errors_are_schema_errors(self):
        for raw in (b'{"code":false,"message":"ok","request_id":"r","data":{}}',b'{"code":0,"message":"ok","request_id":"r","data":{"value":1e999999999999999999999}}'):
            with self.subTest(raw=raw),self.assertRaises(mc.MoneyCraftError) as caught:
                fuyao_client.parse_json(raw)
            self.assertEqual(caught.exception.exit_code,mc.EXIT_SCHEMA)

    def test_nonfinite_retry_after_is_ignored(self):
        for value in ('NaN','Infinity','-Infinity'):
            with self.subTest(value=value):self.assertIsNone(fuyao_client.bounded_retry_after({'Retry-After':value}))

    def test_cleanup_error_preserves_status_without_private_details(self):
        class Body(io.BytesIO):
            def close(self):
                super().close()
                raise OSError('private fixture detail')
        body=Body(b'fixture')
        error=urllib.error.HTTPError('https://fixture.invalid',400,'bad',{},body)
        with self.assertRaises(mc.MoneyCraftError) as caught:
            mc.FuyaoClient('synthetic',opener=FakeOpener([error])).request('snapshot','/snapshot',{})
        self.assertEqual(caught.exception.code,400)
        self.assertIn('cleanup failed',str(caught.exception))
        self.assertNotIn('private fixture detail',str(caught.exception))
        self.assertTrue(body.closed)

    def test_recursive_json_is_schema_error(self):
        with self.assertRaises(mc.MoneyCraftError) as caught:
            fuyao_client.parse_json(b'{"data":'+b'['*2000+b'0'+b']'*2000+b'}')
        self.assertEqual(caught.exception.exit_code,mc.EXIT_SCHEMA)

    def test_length_contract_keeps_exact_body_and_rejects_extra(self):
        raw=b'{"code":0,"message":"ok","request_id":"r","data":{}}'
        for delta in (0,-1):
            opener=FakeOpener([FakeResponse(raw,{'Content-Length':str(len(raw)+delta)})])
            client=mc.FuyaoClient('synthetic',opener=opener)
            if delta==0:self.assertEqual(client.request('snapshot','/snapshot',{}).payload['code'],0)
            else:
                with self.assertRaises(mc.MoneyCraftError) as caught:client.request('snapshot','/snapshot',{})
                self.assertEqual(caught.exception.exit_code,mc.EXIT_SCHEMA)

    def test_redirect_cleanup_failure_preserves_rejection(self):
        from unittest import mock
        class Body(io.BytesIO):
            headers={}
            def close(self):
                if self.closed:return
                super().close()
                raise OSError('private cleanup fixture')
        for oversized in (False,True):
            with self.subTest(oversized=oversized):
                body=Body(b'x'*33 if oversized else b'')
                handler=fuyao_client.SameHostRedirectHandler()
                class Parent:
                    def open(self,*args,**kwargs):raise AssertionError('target must not open')
                handler.add_parent(Parent())
                class Opener:
                    calls=0
                    def open(self,request,timeout):
                        self.calls+=1;request.timeout=timeout
                        return handler.http_error_302(request,body,302,'redirect',{'location':'https://fixture.invalid/next' if oversized else 'http://fixture.invalid/next'})
                opener=Opener()
                with mock.patch.object(fuyao_client,'MAX_RESPONSE_BYTES',32),self.assertRaises(mc.MoneyCraftError) as caught:
                    mc.FuyaoClient('synthetic',base_url='https://fixture.invalid',opener=opener,sleeper=lambda _:None).request('snapshot','/snapshot',{})
                self.assertEqual(caught.exception.kind,'response_too_large' if oversized else 'http_error')
                self.assertEqual(opener.calls,1)
                self.assertIn('cleanup failed',str(caught.exception))
                self.assertNotIn('private cleanup fixture',str(caught.exception))
                self.assertTrue(body.closed)

    def test_redirect_drain_close_failure_is_generic(self):
        class Body(io.BytesIO):
            headers={}
            def close(self):
                if self.closed:return
                super().close()
                raise OSError('private cleanup fixture')
        body=Body(b'')
        handler=fuyao_client.SameHostRedirectHandler()
        class Parent:
            def open(self,*args,**kwargs):raise AssertionError('target must not open after cleanup failure')
        handler.add_parent(Parent())
        req=urllib.request.Request('https://fixture.invalid/start');req.timeout=1
        with self.assertRaises(mc.MoneyCraftError) as caught:
            handler.http_error_302(req,body,302,'redirect',{'location':'https://fixture.invalid/next'})
        self.assertEqual(caught.exception.kind,'local_io_error')
        self.assertNotIn('private cleanup fixture',str(caught.exception))
