#!/usr/bin/env python3
"""Explicit, bounded POSIX launcher for native Codex read-only fixture acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time


DISABLED_FEATURES = (
    'hooks', 'memories', 'multi_agent', 'apps', 'goals', 'plugins',
    'plugin_discovery_prefetch', 'browser_use', 'browser_use_external',
    'browser_use_full_cdp_access', 'computer_use', 'image_generation',
    'in_app_browser', 'in_app_local_automation', 'daemon_auto_start', 'shell_snapshot',
)


def executable(value):
    found = shutil.which(value)
    if not found:
        raise ValueError('Executable not found: ' + value)
    return Path(found).resolve(strict=True)


def capture(argv, cwd, env):
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=10)
    if result.returncode:
        # Tool diagnostics can include configuration values; keep them out of previews.
        raise ValueError('Tool preflight failed: ' + str(argv[0]))
    return result.stdout.strip()


def resolve_git(value, project, env):
    selected = executable(value)
    if sys.platform == 'darwin' and selected == Path('/usr/bin/git'):
        developer = capture(['/usr/bin/xcode-select', '-p'], project, env)
        selected = executable(str(Path(developer) / 'usr/bin/git'))
        if selected == Path('/usr/bin/git'):
            raise ValueError('Select an actual Git executable with --git')
    return selected


def mcp_servers(argv, project, env):
    """Read configuration only; `mcp list` does not start the configured servers."""
    entries = json.loads(capture([*argv, 'mcp', 'list', '--json'], project, env))
    if not isinstance(entries, list) or any(
        not isinstance(entry, dict) or not isinstance(entry.get('name'), str)
        or not isinstance(entry.get('enabled'), bool) for entry in entries
    ):
        raise ValueError('Unrecognized Codex MCP configuration response')
    return entries


def stop_group(process):
    """Stop this launch's POSIX process group, including a child outliving its parent."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        process.wait()
        return
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def plan(args):
    if os.name != 'posix':
        raise ValueError('This manual launcher supports POSIX hosts only')
    if sys.version_info < (3, 11):
        raise ValueError('Run this launcher with Python 3.11 or newer')
    if not 0 < args.timeout <= 300:
        raise ValueError('--timeout must be greater than zero and at most 300 seconds')
    project = args.project.resolve(strict=True)
    if not (project / '.agents/skills/workflow-craft/SKILL.md').is_file():
        raise ValueError('Select a disposable project with its fixed Codex Skill installed')
    output = args.output.resolve()
    if output.is_relative_to(project):
        raise ValueError('--output must be outside the acceptance project')
    if output.exists():
        raise ValueError('--output must be a new directory; preserve earlier attempts')
    prompt = args.prompt_file.read_text(encoding='utf-8')
    if not prompt.strip():
        raise ValueError('The prompt file is empty')

    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0',
               GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
               GIT_TERMINAL_PROMPT='0')
    git = resolve_git(args.git, project, env)
    codex = executable(args.codex)
    python = Path(sys.executable).resolve(strict=True)
    versions = {
        'python': capture([str(python), '--version'], project, env),
        'git': capture([str(git), '--version'], project, env),
        'codex': capture([str(codex), '--version'], project, env),
    }
    root = Path(capture([str(git), 'rev-parse', '--show-toplevel'], project, env)).resolve()
    if root != project:
        raise ValueError('--project must name the Git root of the disposable fixture')

    tools = output / 'tools'
    env['PATH'] = str(tools) + os.pathsep + os.environ.get('PATH', os.defpath)
    project_setting = '{' + json.dumps(str(project), ensure_ascii=False) + ' = { trust_level = "trusted" }}'
    discovery = [str(codex), '-c', 'features.plugins=false', '-c', 'projects=' + project_setting]
    servers = mcp_servers(discovery, project, env)
    # CLI overrides merge tables: an empty table would leave enabled servers intact.
    disabled_servers = '{' + ', '.join(json.dumps(entry['name'], ensure_ascii=False)
                                      + ' = { enabled = false }' for entry in servers) + '}'
    settings = {
        'approval_policy': '"never"',
        'allow_login_shell': 'false',
        'shell_environment_policy.experimental_use_profile': 'false',
        'web_search': '"disabled"',
        'mcp_servers': disabled_servers,
        'projects': project_setting,
    }
    settings.update({'features.' + name: 'false' for name in DISABLED_FEATURES})
    # Explicit sets reach model-generated commands without replacing user startup files.
    for name in ('PATH', 'PYTHONDONTWRITEBYTECODE', 'GIT_OPTIONAL_LOCKS',
                 'GIT_CONFIG_GLOBAL', 'GIT_CONFIG_SYSTEM', 'GIT_TERMINAL_PROMPT'):
        settings['shell_environment_policy.set.' + name] = json.dumps(env[name], ensure_ascii=False)
    argv = [str(codex)]
    for key, value in settings.items():
        argv.extend(['-c', key + '=' + value])
    if any(entry['enabled'] for entry in mcp_servers(argv, project, env)):
        raise ValueError('Refusing model launch: effective MCP configuration is still enabled')
    argv.extend(['exec', '--sandbox', 'read-only', '--ephemeral', '--json', '--color', 'never',
                 '--cd', str(project), '--output-last-message', str(output / 'final.txt'), '-'])
    receipt = dict(status='preview', project=str(project), output=str(output),
                   tools=dict(python=str(python), git=str(git), codex=str(codex)),
                   versions=versions, timeout_seconds=args.timeout, argv=argv,
                   disabled_mcp_servers=len(servers),
                   prompt_sha256=hashlib.sha256(prompt.encode('utf-8')).hexdigest(),
                   model='inherited from current Codex configuration',
                   writes='parent-owned output directory only; no user configuration edits')
    return receipt, env, prompt


def execute(receipt, env, prompt):
    output = Path(receipt['output'])
    output.mkdir(parents=True, exist_ok=False)
    tools = output / 'tools'
    tools.mkdir()
    for name in ('python3', 'git'):
        tools.joinpath(name).symlink_to(receipt['tools']['python' if name == 'python3' else name])
    (output / 'plan.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n',
                                     encoding='utf-8')
    started = time.monotonic()
    status = 'completed'
    with (output / 'events.jsonl').open('wb') as events, (output / 'stderr.log').open('wb') as errors:
        process = subprocess.Popen(receipt['argv'], cwd=receipt['project'], env=env,
                                   stdin=subprocess.PIPE, stdout=events, stderr=errors,
                                   start_new_session=True)
        try:
            process.communicate(prompt.encode('utf-8'), timeout=receipt['timeout_seconds'])
            code = process.returncode if process.returncode >= 0 else 128 - process.returncode
        except subprocess.TimeoutExpired:
            stop_group(process)
            status, code = 'timed_out', 124
        except KeyboardInterrupt:
            stop_group(process)
            status, code = 'interrupted', 130
    result = dict(status=status, exit_code=code, child_exit_code=process.returncode,
                  wall_seconds=round(time.monotonic() - started, 3),
                  acceptance='unverified: inspect native commands, answer and file snapshots')
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--prompt-file', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New directory outside the fixture')
    parser.add_argument('--codex', default='codex')
    parser.add_argument('--git', default='git', help='Git executable; macOS launcher is resolved via xcode-select')
    parser.add_argument('--timeout', type=float, default=300)
    parser.add_argument('--execute', action='store_true', help='Explicitly authorize one model session')
    args = parser.parse_args()
    try:
        receipt, env, prompt = plan(args)
        if args.execute:
            return execute(receipt, env, prompt)
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print('codex_readonly: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
