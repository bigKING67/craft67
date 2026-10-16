#!/usr/bin/env python3
"""Opt-in destructive probe of a disposable, isolated Gitea restore ONLY.

Not part of the Skill runtime or the offline gate. It seeds an empty repository
with synthetic commits and creates local fixture users/PRs/reviews. The caller
must dispose of the restore project afterwards; production is never a target.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import tempfile
import time


API_CLIENT = r'''
import json, pathlib, sys, urllib.request, urllib.error
request = json.load(sys.stdin)
tokens = json.loads(pathlib.Path('/probe-auth/tokens.json').read_text())
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
token = tokens[request['actor']]
if request.get('adapter'):
    sys.path.insert(0, '/twc/scripts')
    from twc_lib.providers.gitea import Gitea
    os = __import__('os')
    os.environ['TWC_PROBE_TOKEN'] = token
    client = Gitea('http://127.0.0.1:3000', request['repository'],
                  token_env='TWC_PROBE_TOKEN', allow_loopback_http=True)
    number = request['number']
    task, change = client.get_task(number), client.get_change(number)
    reviews, checks = client.get_reviews(number), client.get_checks(change['head']['sha'])
    print(json.dumps({'number': task['number'], 'merged': change['merged'],
                      'reviews': len(reviews), 'checks': len(checks),
                      'checks_evidence': 'not_run' if not checks else 'observed'}))
else:
    payload = request.get('body')
    req = urllib.request.Request('http://127.0.0.1:3000/api/v1' + request['path'],
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={'Authorization': 'token ' + token, 'Content-Type': 'application/json'},
        method=request['method'])
    try:
        with opener.open(req, timeout=15) as response:
            data = response.read()
            print(json.dumps({'status': response.status, 'body': json.loads(data) if data else None}))
    except urllib.error.HTTPError as exc:
        data = exc.read()
        print(json.dumps({'status': exc.code, 'body': json.loads(data) if data else None}))
'''


def validate_fixture(context, server, network, project):
    """Fail before credentials or fixture mutations if isolation is absent."""
    env = dict(item.split('=', 1) for item in server['Config']['Env'])
    labels = server['Config']['Labels']
    valid = (
        context['Endpoints']['docker']['Host'].startswith('unix://')
        and labels.get('com.docker.compose.project') == project
        and labels.get('traefik.enable') == 'false'
        and env.get('GITEA__server__ROOT_URL') == 'http://restore.example.invalid/'
        and env.get('GITEA__actions__ENABLED') == 'false'
        and env.get('GITEA__mailer__ENABLED') == 'false'
        and not server['HostConfig']['PortBindings']
        and list(server['NetworkSettings']['Networks']) == [project + '_data']
        and network['Internal']
    )
    volumes = [mount for mount in server['Mounts'] if mount['Type'] == 'volume']
    valid = valid and bool(volumes) and all(m['Name'].startswith(project + '_') for m in volumes)
    valid = valid and all(not m['RW'] for m in server['Mounts'] if m['Type'] == 'bind')
    if not valid:
        raise ValueError('Refusing a non-disposable or non-isolated Gitea fixture')


def finalize_report(report, revocations):
    report['temporary_tokens_revoked'] = bool(revocations) and all(revocations)
    report['fixture_disposal_required'] = True
    if not report['temporary_tokens_revoked']:
        report['status'] = 'incomplete'


def main():
    if not __debug__:
        raise RuntimeError('Do not run behavioral assertions with Python optimization enabled')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--context', required=True)
    parser.add_argument('--project', required=True)
    parser.add_argument('--repository', default='baiqueling/aios')
    parser.add_argument('--owner', default='sixseven')
    parser.add_argument('--python-image', required=True, help='An already-present local image ID containing Python 3.11+')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.apply:
        print(json.dumps({'action': 'disposable local restore policy probe', 'apply': False}))
        return
    if not re.fullmatch(r'twc-gitea-restore-[a-f0-9]{8}', args.project):
        raise ValueError('Only a uniquely named TWC disposable restore is accepted')
    if not re.fullmatch(r'[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+', args.repository):
        raise ValueError('Invalid repository')
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', args.owner):
        raise ValueError('Invalid fixture owner')
    if not re.fullmatch(r'sha256:[a-f0-9]{64}', args.python_image):
        raise ValueError('Use an already-present immutable local Python image ID')
    docker = ['docker', '--context', args.context]

    def run(command, *, data=None, check=True):
        result = subprocess.run(command, input=data, capture_output=True, timeout=60)
        if check and result.returncode:
            raise RuntimeError(f'Command failed ({command[0]}, exit {result.returncode}); raw output withheld')
        return result

    context = json.loads(run(['docker', 'context', 'inspect', args.context]).stdout)[0]
    if not context['Endpoints']['docker']['Host'].startswith('unix://'):
        raise ValueError('A local Unix-socket Docker context is required')
    ids = run(docker + ['ps', '-q', '--filter', 'label=com.docker.compose.project=' + args.project,
                        '--filter', 'label=com.docker.compose.service=server']).stdout.decode().splitlines()
    if len(ids) != 1:
        raise ValueError('Expected exactly one running fixture server')
    container = ids[0]
    info = json.loads(run(docker + ['inspect', container]).stdout)[0]
    networks = list(info['NetworkSettings']['Networks'])
    if networks != [args.project + '_data']:
        raise ValueError('Unexpected fixture network')
    network = json.loads(run(docker + ['network', 'inspect', networks[0]]).stdout)[0]
    validate_fixture(context, info, network, args.project)
    run(docker + ['image', 'inspect', args.python_image])  # Never implicitly pull.
    nonce = secrets.token_hex(4)
    actors = {'owner': args.owner, 'developer': 'twcdev' + nonce, 'reviewer': 'twcreview' + nonce,
              'observer': args.owner}
    work = '/tmp/twc-policy-' + nonce
    package = Path(__file__).resolve().parents[2]
    runtime = package / 'skills/team-workflow-craft'
    checks = []
    report = {'schema': 'team-gitea.policy-probe.v1', 'project': args.project,
              'tested_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'gitea_image': info['Config']['Image'], 'repository': args.repository,
              'scope': 'disposable local restore; synthetic identities and Git content',
              'checks': checks, 'status': 'incomplete'}
    args.output.parent.mkdir(parents=True, exist_ok=True)

    def record(name, **facts):
        checks.append({'name': name, 'status': 'passed', **facts})
        print(json.dumps(checks[-1]), flush=True)

    with tempfile.TemporaryDirectory(prefix='twc-policy-auth-') as secret_dir:
        auth_file = Path(secret_dir) / 'tokens.json'
        tokens = {}

        def api(actor, method, path, body=None, *, adapter=None):
            request = {'actor': actor, 'method': method, 'path': path, 'body': body}
            if adapter:
                request.update(adapter)
            cmd = docker + ['run', '--rm', '-i', '--pull', 'never', '--read-only', '--cap-drop', 'ALL',
                '--security-opt', 'no-new-privileges:true', '--user', f'{os.getuid()}:{os.getgid()}',
                '--network', 'container:' + container, '--mount', f'type=bind,src={secret_dir},dst=/probe-auth,readonly',
                '--mount', f'type=bind,src={runtime},dst=/twc,readonly',
                '--entrypoint', 'python3', args.python_image, '-c', API_CLIENT]
            return json.loads(run(cmd, data=json.dumps(request).encode()).stdout)

        def ok(actor, method, path, body=None, statuses=(200, 201, 204)):
            response = api(actor, method, path, body)
            if response['status'] not in statuses:
                raise RuntimeError(f'{method} {path} returned {response["status"]}')
            return response['body']

        def write_server(path, contents):
            run(docker + ['exec', '-i', container, 'sh', '-c', 'umask 077; cat > "$1"', 'sh', path], data=contents)

        def git(*arguments, actor='developer', check=True, data=None):
            return run(docker + ['exec', '-i', '-e', 'GIT_TERMINAL_PROMPT=0',
                '-e', 'GIT_ASKPASS=' + work + '/askpass', '-e', 'TWC_PROBE_ACTOR=' + actor,
                container, 'git', '-c', 'credential.helper=', '-C', work + '/git', *arguments], data=data, check=check)

        prefix = '/repos/' + args.repository

        def main_sha():
            return ok('owner', 'GET', prefix + '/branches/main')['commit']['id']

        def pull(number):
            return ok('owner', 'GET', prefix + '/pulls/' + str(number))

        def wait_head(number, sha):
            for _ in range(30):
                result = pull(number)
                if result['head']['sha'] == sha and result.get('mergeable'):
                    return result
                time.sleep(0.2)
            raise RuntimeError('Fixture PR did not reach the expected mergeable head')

        def merge(number, actor='owner', force=False):
            return api(actor, 'POST', prefix + f'/pulls/{number}/merge',
                       {'do': 'merge', 'head_commit_id': pull(number)['head']['sha'], 'force_merge': force})

        def blocked_merge(name, number, actor='owner', force=False):
            before = main_sha()
            result = merge(number, actor, force)
            assert 400 <= result['status'] < 500, f'{name}: merge unexpectedly accepted'
            assert not pull(number)['merged'] and main_sha() == before
            record(name, http_status=result['status'], main_unchanged=True)

        def review(number, event='APPROVED'):
            return ok('reviewer', 'POST', prefix + f'/pulls/{number}/reviews',
                      {'event': event, 'body': 'Disposable policy fixture', 'commit_id': pull(number)['head']['sha']})

        def commit_file(name, content):
            write_server(work + '/git/' + name, content.encode())
            git('add', '--', name)
            git('commit', '-m', 'Fixture: ' + name)
            return git('rev-parse', 'HEAD').stdout.decode().strip()

        def open_pull(branch, base, filename):
            git('checkout', '-b', branch, base)
            sha = commit_file(filename, filename + '\n')
            git('push', 'origin', 'HEAD:refs/heads/' + branch)
            pr = ok('developer', 'POST', prefix + '/pulls', {'base': 'main', 'head': branch, 'title': 'Fixture ' + branch})
            wait_head(pr['number'], sha)
            return pr['number']

        try:
            run(docker + ['exec', container, 'mkdir', '-m', '700', work])
            run(docker + ['exec', container, 'mkdir', '-m', '700', work + '/tokens'])
            for actor, username in actors.items():
                if actor in ('developer', 'reviewer'):
                    run(docker + ['exec', container, 'gitea', 'admin', 'user', 'create', '--username', username,
                                 '--email', username + '@example.invalid', '--random-password', '--must-change-password=false'])
                result = run(docker + ['exec', container, 'gitea', 'admin', 'user', 'generate-access-token',
                    '--username', username, '--token-name', 'twc-policy-' + nonce + '-' + actor,
                    '--scopes', ('read:repository,read:issue,read:user' if actor == 'observer'
                                 else 'write:repository,write:issue,read:user'), '--raw'])
                token = result.stdout.decode().strip().splitlines()[-1]
                assert re.fullmatch(r'[a-f0-9]{40}', token)
                tokens[actor] = token
                auth_file.write_text(json.dumps(tokens)); auth_file.chmod(0o600)
                write_server(work + '/tokens/' + actor, token.encode())
            repo = ok('owner', 'GET', prefix)
            assert repo['private'] and repo['empty'], 'Refusing to modify a populated fixture repository'
            policy = ok('owner', 'GET', prefix + '/branch_protections/main')
            expected = {'enable_push': False, 'enable_force_push': False, 'required_approvals': 1,
                        'dismiss_stale_approvals': True, 'block_on_outdated_branch': True,
                        'block_on_rejected_reviews': True, 'block_admin_merge_override': True,
                        'enable_merge_whitelist': True, 'merge_whitelist_usernames': [args.owner],
                        'enable_status_check': False, 'enable_bypass_allowlist': False}
            for key, value in expected.items():
                assert policy[key] == value, 'Unexpected fixture policy: ' + key
            for actor in ('developer', 'reviewer'):
                ok('owner', 'PUT', prefix + '/collaborators/' + actors[actor], {'permission': 'write'})
            askpass = '#!/bin/sh\ncase "$1" in\n*Username*) case "$TWC_PROBE_ACTOR" in\n'
            askpass += ''.join(f'{actor}) printf "%s" "{username}";;\n' for actor, username in actors.items())
            askpass += 'esac;;\n*Password*) cat "' + work + '/tokens/$TWC_PROBE_ACTOR";;\n*) exit 1;;\nesac\n'
            write_server(work + '/askpass', askpass.encode())
            run(docker + ['exec', container, 'chmod', '700', work + '/askpass'])
            run(docker + ['exec', container, 'git', 'init', '-b', 'main', work + '/git'])
            git('config', 'user.name', 'TWC policy fixture'); git('config', 'user.email', 'fixture@example.invalid')
            git('remote', 'add', 'origin', 'http://127.0.0.1:3000/' + args.repository + '.git')
            seed = commit_file('README.md', 'Disposable local policy test. No AIOS source.\n')
            ok('owner', 'PATCH', prefix + '/branch_protections/main',
               {'enable_push': True, 'enable_push_whitelist': True, 'push_whitelist_usernames': [args.owner]})
            try:
                git('push', 'origin', 'HEAD:refs/heads/main', actor='owner')
            finally:
                ok('owner', 'PATCH', prefix + '/branch_protections/main',
                   {'enable_push': False, 'enable_push_whitelist': False, 'push_whitelist_usernames': []})
            record('fixture_seed_and_policy_restored', seed=seed)
            candidate = commit_file('candidate.txt', 'Unreviewed update\n')
            orphan = git('commit-tree', 'HEAD^{tree}', data=b'Unrelated fixture root\n').stdout.decode().strip()
            for name, arguments in [
                ('developer_direct_main_push_denied', ['origin', candidate + ':refs/heads/main']),
                ('developer_non_ff_force_main_push_denied', ['--force', 'origin', orphan + ':refs/heads/main']),
                ('developer_main_deletion_denied', ['origin', ':refs/heads/main'])]:
                result = git('push', *arguments, check=False)
                assert result.returncode != 0 and main_sha() == seed, name
                record(name, git_exit=result.returncode, main_unchanged=True)
            a = open_pull('fixture-a', seed, 'a.txt')
            b = open_pull('fixture-b', seed, 'b.txt')
            record('developer_feature_push_and_pull_requests', pull_requests=[a, b])
            self_review = api('developer', 'POST', prefix + f'/pulls/{a}/reviews', {'event': 'APPROVED', 'body': 'Self approval attempt'})
            assert 400 <= self_review['status'] < 500
            record('author_self_approval_denied', http_status=self_review['status'])
            blocked_merge('owner_merge_without_approval_denied', a)
            blocked_merge('owner_force_merge_without_approval_denied', a, force=True)
            review(a); review(b)
            blocked_merge('developer_merge_outside_allowlist_denied', a, actor='developer')
            git('checkout', 'fixture-a'); updated = commit_file('a.txt', 'Updated after approval\n')
            git('push', 'origin', 'HEAD:refs/heads/fixture-a'); wait_head(a, updated)
            blocked_merge('stale_approval_merge_denied', a)
            review(a)
            assert merge(a)['status'] in (200, 201, 204) and pull(a)['merged']
            record('fresh_approval_owner_merge_passed', pull_request=a)
            blocked_merge('outdated_base_merge_denied', b)
            git('checkout', 'fixture-b'); git('fetch', 'origin', 'main'); git('merge', '--no-edit', 'FETCH_HEAD')
            sha = git('rev-parse', 'HEAD').stdout.decode().strip()
            git('push', 'origin', 'HEAD:refs/heads/fixture-b'); wait_head(b, sha)
            # Gitea dismisses approvals when PR content changes, not on every
            # new SHA. A base-only merge can retain approval of an older head.
            # Team integration still requires fresh combined verification and
            # explicit approval of this head; do not infer that from UI green.
            reviews = ok('owner', 'GET', prefix + f'/pulls/{b}/reviews')
            retained = [r for r in reviews if r['state'] == 'APPROVED' and not r['dismissed']]
            assert retained and all(r['commit_id'] != sha for r in retained)
            record('base_only_update_retains_content_approval', requires_manual_fresh_head_review=True)
            review(b)
            reviews = ok('owner', 'GET', prefix + f'/pulls/{b}/reviews')
            assert any(r['state'] == 'APPROVED' and not r['dismissed'] and r['commit_id'] == sha for r in reviews)
            assert merge(b)['status'] in (200, 201, 204) and pull(b)['merged']
            record('updated_base_and_approval_owner_merge_passed', pull_request=b)
            git('fetch', 'origin', 'main')
            c = open_pull('fixture-c', 'FETCH_HEAD', 'c.txt'); review(c, 'REQUEST_CHANGES')
            blocked_merge('requested_changes_merge_denied', c)
            adapter = api('observer', 'GET', '/', adapter={'adapter': True, 'repository': args.repository, 'number': a})
            assert adapter['number'] == a and adapter['merged'] and adapter['reviews'] > 0
            assert adapter['checks'] == 0 and adapter['checks_evidence'] == 'not_run'
            record('twc_task_change_reviews_checks_live_reads', **adapter)
            denied_write = api('observer', 'POST', prefix + '/issues', {'title': 'This read-only request must be denied'})
            assert denied_write['status'] == 403
            record('twc_readonly_scope_write_denied', http_status=denied_write['status'])
            report['limitations'] = ['No real CI or combined product tests ran',
                'Base-only updates retain content approval; integration owner must verify exact head/base',
                'Synthetic accounts in an isolated local restore are not a real multi-person host pilot']
            report['status'] = 'passed'
        finally:
            revoked = []
            for actor in tokens:
                try:
                    result = api(actor, 'DELETE', '/token')
                    denied = api(actor, 'GET', '/user')
                    revoked.append(result['status'] == 204 and denied['status'] in (401, 403))
                except Exception:
                    revoked.append(False)
            finalize_report(report, revoked)
            args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
            args.output.chmod(0o600)
            if not report['temporary_tokens_revoked']:
                raise RuntimeError('Temporary token revocation incomplete; dispose of the isolated restore')
    print(json.dumps({'status': report['status'], 'checks': len(checks), 'receipt': str(args.output)}))


if __name__ == '__main__':
    main()
