from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from .models import HelseIDProfile
from requests_oauth2client.tokens import IdToken


class HelseIDBackend(BaseBackend):
    def authenticate(self, request, id_token_payload: IdToken = None):
        if id_token_payload is None:
            return None

        subject = id_token_payload.subject

        try:
            profile = HelseIDProfile.objects.get(subject=subject)
            return profile.user
        except HelseIDProfile.DoesNotExist:
            given_name = id_token_payload.get_claim("given_name") or ""
            middle_name = id_token_payload.get_claim("middle_name") or ""
            family_name = id_token_payload.get_claim("family_name") or ""
            hpr_number = id_token_payload.get_claim("helseid://claims/hpr/hpr_number")

            first_name = f"{given_name} {middle_name}".strip() if middle_name else given_name

            user = get_user_model().objects.create_user(
                username=subject,
                first_name=first_name,
                last_name=family_name,
            )
            HelseIDProfile.objects.create(
                user=user,
                subject=subject,
                hpr_number=hpr_number,
            )
            return user

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
