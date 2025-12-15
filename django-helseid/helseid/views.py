import json
from requests_oauth2client import OAuth2Client, AuthorizationRequest
import requests

from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import HttpResponse
from django.core.cache import cache
from django.conf import settings


def home(request):
    user = request.session.get("user")
    if user:
        user = json.dumps(user)
    return render(request, "helseid/home.html", context={"user": user})


def login(request):
    # Bygg redirect URLen til din callback view
    django_redirect_uri = request.build_absolute_uri(reverse("auth"))
    
    # get server_metadata
    cache_key = "helseid_server_metadata"
    nhn_server_metadata = cache.get(cache_key)
    if not nhn_server_metadata:
        response = requests.get(settings.HELSEID_SERVER_METADATA_URL)
        response.raise_for_status()
        nhn_server_metadata = response.json()
        # Cache for 24 hours
        cache.set(cache_key, nhn_server_metadata, 60 * 60 * 24)


    client = OAuth2Client(
        token_endpoint=nhn_server_metadata["token_endpoint"],
        authorization_endpoint=nhn_server_metadata["pushed_authorization_request_endpoint"],
        client_id=settings.HELSEID_CLIENT_ID,
        client_jwk=settings.HELSEID_CLIENT_SECRET,
    )


    print(client.authorization_endpoint)
    az_request = client.authorization_request(scope="openid")
    print(az_request)


    # print(oauth2client)



    return HttpResponse("yay")


def auth(request):

    # Do auth stuff

    return redirect("home")
