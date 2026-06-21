from datetime import datetime, timezone
import json
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse
from requests_oauth2client import OAuth2Client, PrivateKeyJwt

from jwskate import Jwt


HELSEID_ENVIRONMENTS = {
    'test': 'https://helseid-sts.test.nhn.no/.well-known/openid-configuration',
    'production': 'https://helseid-sts.nhn.no/.well-known/openid-configuration',
}


def get_server_metadata_url() -> str:
    config = settings.HELSEID
    if 'SERVER_METADATA_URL' in config:
        return config['SERVER_METADATA_URL']
    return HELSEID_ENVIRONMENTS[config['ENVIRONMENT']]


def get_sts_url() -> str:
    parsed = urlparse(get_server_metadata_url())
    return f"{parsed.scheme}://{parsed.netloc}"


class CustomPrivateKeyJwt(PrivateKeyJwt):

    def __init__(self, *args, sts_url: str, **kwargs):
        super().__init__(*args, **kwargs)
        object.__setattr__(self, 'sts_url', sts_url)

    def client_assertion(self, audience: str) -> str:
        """Generate a Client Assertion, asymmetrically signed with `private_jwk` as key.

        Args:
            audience: ignored; the HelseID STS URL from config is used instead,
                      because HelseID requires the bare STS base URL, not the
                      token endpoint path that requests_oauth2client passes here.

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
                "aud": self.sts_url,
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
    redirect_uri = request.build_absolute_uri(reverse("auth"))

    if settings.HELSEID.get('USE_DUMMY_SERVER_METADATA', False):
        with open(settings.HELSEID['DUMMY_SERVER_METADATA_PATH']) as f:
            server_metadata = json.load(f)
    else:
        cache_key = "helseid_server_metadata"
        server_metadata = cache.get(cache_key)
        if not server_metadata:
            response = requests.get(get_server_metadata_url())
            response.raise_for_status()
            server_metadata = response.json()
            cache.set(cache_key, server_metadata, 60 * 60 * 24)

    auth = CustomPrivateKeyJwt(
        client_id=settings.HELSEID['CLIENT_ID'],
        private_jwk=settings.HELSEID['CLIENT_SECRET'],
        lifetime=10,
        sts_url=get_sts_url(),
    )
    client = OAuth2Client.from_discovery_document(
        discovery=server_metadata,
        redirect_uri=redirect_uri,
        auth=auth,
        dpop_bound_access_tokens=True,
    )

    client.update_authorization_server_public_keys()
    assert client.authorization_server_jwks, "client.authorization_server_jwks must not be empty"
    return client
