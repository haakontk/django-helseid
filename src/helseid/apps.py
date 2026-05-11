from django.apps import AppConfig
from django.core import checks


class HelseidConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'helseid'
    verbose_name = "HelseID Authentication"

    def ready(self):
        from . import checks as helseid_checks
        checks.register(helseid_checks.check_helseid_settings, checks.Tags.security)
