import json
from requests_oauth2client.exceptions import OAuth2Error

from django.conf import settings
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import authenticate, login as django_login
import datetime
from .utils import get_helseid_client


def home(request):
    user = request.session.get("user")
    if user:
        user = json.dumps(user)
    return render(request, "helseid/home.html", context={"user": user})


def login(request):
    client = get_helseid_client(
        request
    )
    scope = " ".join(settings.HELSEID["SCOPE"])

    az_request = client.authorization_request(
        scope=scope,
        # prompt='login',
    )

    # Store state, nonce and code_verifier in session to validate callback later
    request.session["helseid_state"] = az_request.state
    request.session["helseid_nonce"] = az_request.nonce
    request.session["helseid_code_verifier"] = az_request.code_verifier
    try:
        par_response = client.pushed_authorization_request(az_request)
        return redirect(par_response.uri)
    except OAuth2Error as e:
        error_response = "No response body."
        if e.response is not None:
            error_response = e.response.text

        print(f"Error during PAR request: {e}")
        print(f"HelseID server response: {error_response}")
        return HttpResponse("Failed to initiate login.", status=500)


def auth(request):
    client = get_helseid_client(
        request
    )

    state = request.session.get("helseid_state")
    nonce = request.session.get("helseid_nonce")
    code_verifier = request.session.get("helseid_code_verifier")

    if not state or not nonce or not code_verifier:
        return HttpResponse("Missing authentication session data.", status=400)

    az_request = client.authorization_request(
        scope="openid", state=state, nonce=nonce, code_verifier=code_verifier
    )

    az_response = az_request.validate_callback(request.build_absolute_uri())

    token = client.authorization_code(
        az_response,
    )

    id_token = token.id_token

    # NEXT: VERIFY ID_TOKEN
    subject = id_token.subject
    auth_datetime = id_token.auth_datetime
    given_name = id_token.get_claim("given_name")
    family_name = id_token.get_claim("family_name")
    middle_name = id_token.get_claim("middle_name")
    hpr_number = id_token.get_claim("helseid://claims/hpr/hpr_number")

    print(f"Subject: {subject}")
    print(f"Given Name: {given_name}")
    print(f"Family Name: {family_name}")
    print(f"Middle Name: {middle_name}")
    print(f"HPR Number: {hpr_number}")
    print(f"Auth Datetime: {auth_datetime}")



    user = authenticate(request, id_token_payload=id_token)
    print(user)
    return HttpResponse("All good .", status=200)


    if user:
        django_login(request, user)
        # Set session expiry to 2 hours from auth_datetime
        session_expiry = auth_datetime + datetime.timedelta(hours=2)
        request.session.set_expiry(session_expiry)

        # Clean up temporary authentication data
        del request.session["helseid_state"]
        del request.session["helseid_nonce"]
        del request.session["helseid_code_verifier"]

        return redirect("home")
    else:
        return HttpResponse("Authentication failed.", status=403)



@csrf_exempt
def dummy_token_endpoint(request):
    from urllib.parse import parse_qs

    print("--- DUMMY TOKEN ENDPOINT HIT ---")
    print(f"Request Method: {request.method}")
    print("Request Headers:")
    for header, value in request.headers.items():
        print(f"  {header}: {value}")
    print("Request Body:")
    # print(request.body.decode('utf-8'))

    # TODO
    # Verify that keys are the same as stated in https://utviklerportal.nhn.no/informasjonstjenester/helseid/bruksmoenstre-og-eksempelkode/bruk-av-helseid/docs/teknisk-referanse/endepunkt/token-endepunktet_no_nbmd
    for key, value in parse_qs(request.body.decode("utf-8")).items():
        print(key, value)

    print("--- END DUMMY TOKEN ENDPOINT ---")

    response_data = {
        "identity_token": "123",
        "refresh_token": "123",
        "rt_expires_in": 123,
        "scope": "openid",
        "rejected_scope": "",
    }
    return JsonResponse(response_data, status=201)
