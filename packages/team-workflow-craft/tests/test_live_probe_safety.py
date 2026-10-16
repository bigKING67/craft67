"""Offline rejection tests for the opt-in destructive local policy probe."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('gitea_policy_probe', Path(__file__).parent / 'live/gitea_policy_probe.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ProbeSafetyTests(unittest.TestCase):
    def setUp(self):
        self.project = 'twc-gitea-restore-a1b2c3d4'
        self.context = {'Endpoints': {'docker': {'Host': 'unix:///fixture/docker.sock'}}}
        self.server = {
            'Config': {'Env': ['GITEA__server__ROOT_URL=http://restore.example.invalid/',
                               'GITEA__actions__ENABLED=false', 'GITEA__mailer__ENABLED=false'],
                       'Labels': {'com.docker.compose.project': self.project, 'traefik.enable': 'false'}},
            'HostConfig': {'PortBindings': {}},
            'NetworkSettings': {'Networks': {self.project + '_data': {}}},
            'Mounts': [{'Type': 'volume', 'Name': self.project + '_data', 'RW': True},
                       {'Type': 'bind', 'Source': '/fixture/secret', 'RW': False}]}
        self.network = {'Internal': True}

    def validate(self):
        probe.validate_fixture(self.context, self.server, self.network, self.project)

    def test_accepts_local_isolated_fixture(self):
        self.validate()

    def test_rejects_remote_docker_context(self):
        self.context['Endpoints']['docker']['Host'] = 'ssh://production'
        with self.assertRaises(ValueError): self.validate()

    def test_rejects_production_url_or_active_automations(self):
        original = copy.deepcopy(self.server['Config']['Env'])
        for index, value in enumerate(['GITEA__server__ROOT_URL=https://git.example.com/',
                                       'GITEA__actions__ENABLED=true', 'GITEA__mailer__ENABLED=true']):
            with self.subTest(index=index):
                self.server['Config']['Env'] = original.copy()
                self.server['Config']['Env'][index] = value
                with self.assertRaises(ValueError): self.validate()

    def test_rejects_proxy_and_host_port(self):
        self.server['Config']['Labels']['traefik.enable'] = 'true'
        with self.assertRaises(ValueError): self.validate()
        self.server['Config']['Labels']['traefik.enable'] = 'false'
        self.server['HostConfig']['PortBindings'] = {'3000/tcp': [{'HostPort': '3000'}]}
        with self.assertRaises(ValueError): self.validate()

    def test_rejects_external_or_additional_network(self):
        self.network['Internal'] = False
        with self.assertRaises(ValueError): self.validate()
        self.network['Internal'] = True
        self.server['NetworkSettings']['Networks']['edge'] = {}
        with self.assertRaises(ValueError): self.validate()

    def test_rejects_production_volume_or_writable_host_bind(self):
        self.server['Mounts'][0]['Name'] = 'team-gitea_data'
        with self.assertRaises(ValueError): self.validate()
        self.server['Mounts'][0]['Name'] = self.project + '_data'
        self.server['Mounts'][1]['RW'] = True
        with self.assertRaises(ValueError): self.validate()

    def test_rejects_mismatched_project(self):
        self.server['Config']['Labels']['com.docker.compose.project'] = 'team-gitea'
        with self.assertRaises(ValueError): self.validate()

    def test_failed_or_missing_cleanup_cannot_report_pass(self):
        for revocations in ([], [True, False], [False]):
            with self.subTest(revocations=revocations):
                report = {'status': 'passed'}
                probe.finalize_report(report, revocations)
                self.assertEqual(report['status'], 'incomplete')
                self.assertFalse(report['temporary_tokens_revoked'])
        report = {'status': 'incomplete'}
        probe.finalize_report(report, [True, True])
        self.assertEqual(report['status'], 'incomplete')
        self.assertTrue(report['temporary_tokens_revoked'])


if __name__ == '__main__':
    unittest.main()
