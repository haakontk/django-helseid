import requests
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse
from requests_oauth2client import OAuth2Client, PrivateKeyJwt


def get_helseid_client(request):
    """
    Initializes and returns an OAuth2Client for HelseID.
    It caches the server metadata to avoid fetching it on every request.
    """
    # Build the absolute redirect URI for the auth callback
    redirect_uri = request.build_absolute_uri(reverse("auth"))

    # Get server_metadata from cache or fetch it
    cache_key = "helseid_server_metadata"
    server_metadata = cache.get(cache_key)
    if not server_metadata:
        response = requests.get(settings.HELSEID_SERVER_METADATA_URL)
        response.raise_for_status()
        server_metadata = response.json()
        # Cache for 24 hours
        cache.set(cache_key, server_metadata, 60 * 60 * 24)

    auth = PrivateKeyJwt(
        client_id=settings.HELSEID_CLIENT_ID,
        private_jwk=settings.HELSEID_CLIENT_SECRET,
        lifetime=10
    )
    return OAuth2Client.from_discovery_document(
        discovery=server_metadata,
        redirect_uri=redirect_uri,
        auth=auth
    )