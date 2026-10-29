"""Observe the current operator; never infer identity from task ownership or a branch."""
import re

from .models import now
from .providers import from_config, ProviderError
from .workspace import git

MEMBER_NAME_PROMPT = '请提供你在这个项目中使用的名字或称呼（例如“67”），首次接入只需名字。'


def _valid_name(name):
    return isinstance(name, str) and bool(name.strip()) and not any(ord(char) < 32 or ord(char) == 127 for char in name)


def member_name(root):
    """Read the onboarding name without requiring a complete Git commit identity."""
    name = git(root, 'config', '--get', 'user.name', allowed=(0, 1)).decode('utf-8', errors='replace').strip()
    valid = _valid_name(name)
    return dict(status='available' if valid else 'missing', name=name if valid else None,
                source='git_config_user_name', trust='self_asserted')


def git_identity(root):
    identities = {}
    for role in ('author', 'committer'):
        # Include environment overrides, but refuse Git's implicit OS/hostname guesses.
        raw = git(root, '-c', 'user.useConfigOnly=true', 'var', f'GIT_{role.upper()}_IDENT',
                  allowed=(0, 1, 128)).decode('utf-8', errors='replace').strip()
        match = re.fullmatch(r'([^\r\n<>]+) <([^\r\n<>]+)> -?\d+ [+-]\d{4}', raw)
        identities[role] = dict(name=match[1], email=match[2]) if match else None
    return dict(status='available' if all(identities.values()) else 'incomplete',
                source='effective_git_ident', trust='self_asserted', **identities)


def account(value, provider='gitea'):
    """Keep only the stable account id, login and optional human-readable name."""
    if not isinstance(value, dict):
        return None
    identifier = value.get('id')
    valid_id = (type(identifier) is int and identifier > 0) if provider == 'gitea' else (
        provider == 'cnb' and isinstance(identifier, str)
        and re.fullmatch(r'[A-Za-z0-9_-]{1,128}', identifier) is not None)
    if (not valid_id
            or not isinstance(value.get('login'), str)
            or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,254}', value['login'])):
        return None
    name = value.get('full_name')
    if not isinstance(name, str) or len(name) > 255 or any(ord(c) < 32 or ord(c) == 127 for c in name):
        name = None
    return dict(id=value['id'], login=value['login'], full_name=name or None)


def snapshot(root, config, online=False):
    source = config['coordination']
    platform = dict(provider=source['provider'], instance=source['base_url'].rstrip('/'),
                    status='not_requested', observed_at=None, data=None)
    if source.get('identity_token_env'):
        platform['credential_binding'] = 'separate_identity_token; repository_and_push_identity_unverified'
    if online:
        api = from_config(config)
        try:
            data = account(api.get_identity(), source['provider'])
            platform.update(status='observed' if data else 'invalid_response', data=data)
        except ProviderError as exc:
            platform['status'] = exc.code
        platform['observed_at'] = now()
    return dict(observed_at=now(), member=member_name(root), platform=platform, git=git_identity(root),
                trust='local_observation_not_identity_attestation')


def attributed(actor, instance=None, provider=None):
    if not isinstance(actor, dict):
        return False
    platform = actor.get('platform')
    return (isinstance(platform, dict) and platform.get('provider') in ('gitea', 'cnb')
            and (provider is None or platform.get('provider') == provider)
            and platform.get('status') == 'observed'
            and (instance is None or platform.get('instance') == instance)
            and account(platform.get('data'), platform['provider']) is not None)


def label(actor):
    member = actor.get('member') if isinstance(actor, dict) else None
    name = member.get('name') if isinstance(member, dict) and member.get('status') == 'available' else None
    # Stored records are untrusted input; names must not inject Markdown into handoffs.
    name = re.sub(r'([\\`*_{}\[\]<>()!|#])', r'\\\1', name.strip()) if _valid_name(name) else None
    if not attributed(actor):
        return (f'{name} (self-reported name; platform identity unverified)' if name
                else 'unknown (platform identity unverified)')
    user = actor['platform']['data']
    return f'{user["login"]} (self-reported name: {name})' if name else user['login']
