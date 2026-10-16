"""Parse the companion Compose example without pulling images or starting services."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

PACKAGE = Path(__file__).resolve().parents[1]


class GiteaDeploymentTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('docker'), 'Compose parser unavailable; no Docker runtime test implied')
    def test_isolated_stack_and_private_defaults(self):
        version = subprocess.run(['docker', 'compose', 'version'], capture_output=True, timeout=15)
        if version.returncode:
            self.skipTest('Docker Compose parser unavailable')
        env = dict(os.environ, GITEA_DOMAIN='git.example.invalid',
                   GITEA_SECRET_DIR='/tmp/twc-config-test-no-secrets',
                   TRAEFIK_NETWORK='fixture-edge', TRAEFIK_CERT_RESOLVER='fixture-resolver')
        result = subprocess.run(['docker', 'compose', '--project-name', 'twc-config-test',
                                 '-f', str(PACKAGE / 'examples/gitea/compose.yaml'),
                                 'config', '--format', 'json'], env=env, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        model = json.loads(result.stdout)
        self.assertEqual(set(model['services']), {'server', 'db'})
        server, db = model['services']['server'], model['services']['db']
        for service in (server, db):
            self.assertRegex(service['image'], r'@sha256:[a-f0-9]{64}$')
            self.assertFalse(service.get('ports'))
            self.assertFalse(service.get('privileged'))
            self.assertNotIn('docker.sock', json.dumps(service))
            self.assertTrue(service['mem_limit'])
            self.assertTrue(service['cpus'])
            self.assertTrue(service['pids_limit'])
        self.assertEqual(set(db['networks']), {'data'})
        self.assertTrue(model['networks']['data']['internal'])
        self.assertTrue(model['networks']['edge']['external'])
        settings = server['environment']
        for name in ('GITEA__security__INSTALL_LOCK', 'GITEA__service__DISABLE_REGISTRATION',
                     'GITEA__service__REQUIRE_SIGNIN_VIEW', 'GITEA__repository__FORCE_PRIVATE',
                     'GITEA__server__DISABLE_SSH'):
            self.assertEqual(settings[name], 'true')
        self.assertEqual(settings['GITEA__actions__ENABLED'], 'false')
        self.assertEqual(settings['GITEA__database__HOST'], 'db:5432')
        self.assertNotIn('GITEA__database__PASSWD', settings)
        self.assertNotIn('POSTGRES_PASSWORD', db['environment'])
        self.assertEqual(settings['GITEA__server__ROOT_URL'], 'https://git.example.invalid/')
        self.assertEqual(server['labels']['traefik.docker.network'], 'fixture-edge')
        self.assertEqual(server['labels']['traefik.http.routers.team-gitea.tls.certresolver'], 'fixture-resolver')
        self.assertEqual(set(model['volumes']), {'data', 'config', 'postgres'})
        self.assertEqual(set(model['secrets']), {'db_password', 'secret_key', 'internal_token'})

    @unittest.skipUnless(shutil.which('docker'), 'Compose parser unavailable; no Docker runtime test implied')
    def test_restore_cannot_join_production_proxy_or_volumes(self):
        version = subprocess.run(['docker', 'compose', 'version'], capture_output=True, timeout=15)
        if version.returncode:
            self.skipTest('Docker Compose parser unavailable')
        env = dict(os.environ, GITEA_DOMAIN='git.example.invalid',
                   GITEA_SECRET_DIR='/tmp/twc-restore-test-no-secrets')
        result = subprocess.run(['docker', 'compose', '--project-name', 'twc-restore-fixture',
                                 '-f', str(PACKAGE / 'examples/gitea/compose.yaml'),
                                 '-f', str(PACKAGE / 'examples/gitea/restore.override.yaml'),
                                 'config', '--format', 'json'], env=env, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        model = json.loads(result.stdout)
        self.assertEqual(set(model['networks']), {'data'})
        self.assertTrue(model['networks']['data']['internal'])
        for service in model['services'].values():
            self.assertEqual(set(service['networks']), {'data'})
            self.assertFalse(service.get('ports'))
        server = model['services']['server']
        self.assertEqual(server['labels'], {'traefik.enable': 'false'})
        self.assertEqual(server['environment']['GITEA__server__ROOT_URL'], 'http://restore.example.invalid/')
        self.assertTrue(all(v['name'].startswith('twc-restore-fixture_') for v in model['volumes'].values()))


if __name__ == '__main__':
    unittest.main()
