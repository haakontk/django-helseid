import json
from requests_oauth2client import PrivateKeyJwt
from requests_oauth2client.exceptions import OAuth2Error

from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import HttpResponse, JsonResponse

from django.conf import settings

from .utils import get_helseid_client

def home(request):
    user = request.session.get("user")
    if user:
        user = json.dumps(user)
    return render(request, "helseid/home.html", context={"user": user})


def login(request):
    client = get_helseid_client(request)

    # audience = client.issuer
    # client_assertion = client.auth.client_assertion(audience)
    # print(client_assertion)
    az_request = client.authorization_request(
        scope="openid profile",
        # client_assertion=client_assertion,
        # client_assertion_type="urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
    )

    try:
        par_az_request = client.pushed_authorization_request(az_request)
        print(par_az_request.uri)
    except OAuth2Error as e:
        error_response = "No response body."
        if e.response:
            error_response = e.response.text

        print(f"Error during PAR request: {e}")
        print(f"HelseID server response: {error_response}")

    return JsonResponse(az_request.as_dict())

    # return HttpResponse(par_az_request.uri)

def auth(request):

    # Do auth stuff

    return redirect("home")
