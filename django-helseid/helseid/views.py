import json
from requests_oauth2client import PrivateKeyJwt
from requests_oauth2client.exceptions import OAuth2Error

from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt


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
        scope="openid",
        # client_assertion=client_assertion,
        # client_assertion_type="urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
    )

    print(az_request.args)

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

@csrf_exempt
def dummy_par_endpoint(request):
    print("--- DUMMY PAR ENDPOINT HIT ---")
    print(f"Request Method: {request.method}")
    print("Request Headers:")
    for header, value in request.headers.items():
        print(f"  {header}: {value}")
    print("Request Body:")
    print(request.body.decode('utf-8'))
    print("--- END DUMMY PAR ENDPOINT ---")

    response_data = {
        "request_uri": "dummy_uri",
        "expires_in": 90,  # Lifetime of the request_uri in seconds
    }
    return JsonResponse(response_data, status=201)


def auth(request):

    # Do auth stuff

    return redirect("home")
