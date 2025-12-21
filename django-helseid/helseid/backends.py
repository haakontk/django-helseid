from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from .models import HelseIDProfile  # We will create this in step 2

class HelseIDBackend(BaseBackend):
    def authenticate(self, request, id_token_payload=None):
        if not id_token_payload:
            return None

        # 'sub' is the unique, persistent ID for the user in HelseID
        helseid_sub = id_token_payload.get('sub')
        
        try:
            # Look up the profile connecting HelseID to a Django get_user_model()
            profile = HelseIDProfile.objects.get(helse_id_sub=helseid_sub)
            return profile.user
        except HelseIDProfile.DoesNotExist:
            # Auto-create user if they don't exist
            # You can extract email/name from id_token claims if present
            username = f"helseid_{helseid_sub[:15]}" 
            user = get_user_model().objects.create_user(username=username)
            
            HelseIDProfile.objects.create(
                user=user, 
                helse_id_sub=helseid_sub
            )
            return user

    def get_user(self, user_id):
        try:
            return get_user_model().objects.get(pk=user_id)
        except get_user_model().DoesNotExist:
            return None