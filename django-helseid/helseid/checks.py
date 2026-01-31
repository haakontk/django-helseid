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
    return errors
