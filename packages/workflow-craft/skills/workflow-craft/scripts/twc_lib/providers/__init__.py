"""Read-only source-control providers used by Workflow Craft."""

from .gitea import Gitea, ProviderError
from .cnb import CNB

PROVIDERS = {'gitea': Gitea, 'cnb': CNB}


def from_config(config):
    source = config['coordination']
    kind = source['provider']
    if kind not in PROVIDERS:
        raise ProviderError('unsupported', 'Unsupported collaboration provider')
    options = {'identity_token_env': source['identity_token_env']} if 'identity_token_env' in source else {}
    return PROVIDERS[kind](source['base_url'], source['repository'],
                           source.get('token_env', f'TWC_{kind.upper()}_TOKEN'), **options)


__all__ = ["Gitea", "CNB", "ProviderError", "from_config"]
