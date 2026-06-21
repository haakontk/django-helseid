from django.core import checks
from django.conf import settings

from .utils import HELSEID_ENVIRONMENTS


def check_helseid_settings(app_configs, **kwargs):
    errors = []
    if not hasattr(settings, 'HELSEID'):
        errors.append(
            checks.Error(
                'HELSEID setting is missing.',
                hint='Add HELSEID = { ... } to your settings.py.',
                obj='settings',
                id='helseid.E001',
            )
        )
    else:
        for key in ['CLIENT_ID', 'CLIENT_SECRET', 'SCOPE']:
            if key not in settings.HELSEID:
                errors.append(
                    checks.Error(
                        f'HELSEID setting is missing required key: {key}',
                        obj='settings',
                        id=f'helseid.E002_{key}',
                    )
                )

        has_environment = 'ENVIRONMENT' in settings.HELSEID
        has_url = 'SERVER_METADATA_URL' in settings.HELSEID

        if not has_environment and not has_url:
            valid = ', '.join(f"'{k}'" for k in HELSEID_ENVIRONMENTS)
            errors.append(
                checks.Error(
                    "HELSEID setting is missing required key: ENVIRONMENT (or SERVER_METADATA_URL).",
                    hint=f"Set ENVIRONMENT to one of: {valid}. Or set SERVER_METADATA_URL explicitly.",
                    obj='settings',
                    id='helseid.E002_SERVER_METADATA_URL',
                )
            )
        elif has_environment and settings.HELSEID['ENVIRONMENT'] not in HELSEID_ENVIRONMENTS:
            valid = ', '.join(f"'{k}'" for k in HELSEID_ENVIRONMENTS)
            errors.append(
                checks.Error(
                    f"HELSEID['ENVIRONMENT'] has an invalid value. Must be one of: {valid}.",
                    hint=f"Set ENVIRONMENT to one of: {valid}.",
                    obj='settings',
                    id='helseid.E002_ENVIRONMENT',
                )
            )

    if 'helseid.backends.HelseIDBackend' not in settings.AUTHENTICATION_BACKENDS:
        errors.append(
            checks.Error(
                "'helseid.backends.HelseIDBackend' is missing from AUTHENTICATION_BACKENDS.",
                hint="Add 'helseid.backends.HelseIDBackend' to AUTHENTICATION_BACKENDS in your settings.py.",
                obj='settings',
                id='helseid.E003',
            )
        )

    if not hasattr(settings, 'LOGIN_REDIRECT_URL'):
        errors.append(
            checks.Warning(
                "LOGIN_REDIRECT_URL is not set.",
                hint="You might want to set LOGIN_REDIRECT_URL in settings.py to control where users are redirected after login. Default is '/'.",
                obj='settings',
                id='helseid.W001',
            )
        )
    return errors
