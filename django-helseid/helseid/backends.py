from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from .models import HelseIDProfile
from requests_oauth2client.tokens import IdToken  # We will create this in step 2

class HelseIDBackend(BaseBackend):
    def authenticate(self, request, id_token_payload: IdToken = None):
        if not id_token_payload:
            return None

        subject = id_token_payload.subject
        given_name = id_token_payload.get_claim("given_name")
        family_name = id_token_payload.get_claim("family_name")
        middle_name = id_token_payload.get_claim("middle_name")
        hpr_number = id_token_payload.get_claim("helseid://scopes/hpr/hpr_number")
        
        try:
            # Look up the profile connecting HelseID to a Django get_user_model()
            profile = HelseIDProfile.objects.get(subject=subject)
            return profile.user
        except HelseIDProfile.DoesNotExist:
            # Auto-create user if they don't exist
            # You can extract email/name from id_token claims if present
            username = f"subject"
            first_name = given_name + " " + middle_name
            user = get_user_model().objects.create_user(username=username, first_name=first_name, last_name=family_name)
            
            HelseIDProfile.objects.create(
                user=user, 
                subject=subject,
                hpr_number=hpr_number
            )
            return user

    def get_user(self, user_id):
        try:
            return get_user_model().objects.get(pk=user_id)
        except get_user_model().DoesNotExist:
            return None