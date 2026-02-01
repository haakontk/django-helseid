from django.core import checks
from django.conf import settings

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
        required_keys = ['CLIENT_ID', 'CLIENT_SECRET', 'SCOPE', 'SERVER_METADATA_URL']
        for key in required_keys:
            if key not in settings.HELSEID:
                errors.append(
                    checks.Error(
                        f'HELSEID setting is missing required key: {key}',
                        obj='settings',
                        id=f'helseid.E002_{key}',
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
