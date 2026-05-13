from datetime import datetime, timezone
import json

import requests
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse
from requests_oauth2client import OAuth2Client, PrivateKeyJwt

from jwskate import Jwt


class CustomPrivateKeyJwt(PrivateKeyJwt):

    def client_assertion(self, audience: str) -> str:
        """Generate a Client Assertion, asymmetrically signed with `private_jwk` as key.

        Args:
            audience: the audience to use for the generated Client Assertion.

        Returns:
            a Client Assertion.

        """
        iat = int(datetime.now(tz=timezone.utc).timestamp())
        exp = iat + self.lifetime
        jti = str(self.jti_gen())

        jwt = Jwt.sign(
            claims={
                "iss": self.client_id,
                "sub": self.client_id,
                "aud": "https://helseid-sts.test.nhn.no",
                "iat": iat,
                "exp": exp,
                "nbf": iat,
                "jti": jti,
            },
            key=self.private_jwk,
            alg=self.alg,
            typ="client-authentication+jwt"
        )
        return str(jwt)
    


def get_helseid_client(request):
    """
    Initializes and returns an OAuth2Client for HelseID.
    It caches the server metadata to avoid fetching it on every request.
    """
    # Build the absolute redirect URI for the auth callback
    redirect_uri = request.build_absolute_uri(reverse("auth"))

    if settings.HELSEID.get('USE_DUMMY_SERVER_METADATA', False):
        with open(settings.HELSEID['DUMMY_SERVER_METADATA_PATH']) as f:
            server_metadata = json.load(f)
    else:
        # Get server_metadata from cache or fetch it
        cache_key = "helseid_server_metadata"
        server_metadata = cache.get(cache_key)
        if not server_metadata:
            response = requests.get(settings.HELSEID['SERVER_METADATA_URL'])
            response.raise_for_status()
            server_metadata = response.json()
            # Cache for 24 hours
            cache.set(cache_key, server_metadata, 60 * 60 * 24)

    auth = CustomPrivateKeyJwt(
        client_id=settings.HELSEID['CLIENT_ID'],
        private_jwk=settings.HELSEID['CLIENT_SECRET'],
        lifetime=10
    )
    client = OAuth2Client.from_discovery_document(
        discovery=server_metadata,
        redirect_uri=redirect_uri,
        auth=auth,
        dpop_bound_access_tokens=True, 
    )

    # Fetch public keys from NHN
    client.update_authorization_server_public_keys()
    assert client.authorization_server_jwks, "client.authorization_server_jwks must not be empty"
    return client
