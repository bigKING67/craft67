"""Observe the current operator; never infer identity from task ownership or a branch."""
import re

from .models import now
from .providers import from_config, ProviderError
from .workspace import git


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
    return dict(observed_at=now(), platform=platform, git=git_identity(root),
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
    if not attributed(actor):
        return 'unknown (platform identity unverified)'
    user = actor['platform']['data']
    return user['login']
