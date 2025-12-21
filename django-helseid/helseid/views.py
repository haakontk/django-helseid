import json
from requests_oauth2client.exceptions import OAuth2Error

from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from .utils import get_helseid_client

USE_DUMMY_SERVER_METADATA = False


def home(request):
    user = request.session.get("user")
    if user:
        user = json.dumps(user)
    print(f"Current session data: {dict(request.session)}")
    return render(request, "helseid/home.html", context={"user": user})


def login(request):
    client = get_helseid_client(
        request, use_dummy_server_metadata=USE_DUMMY_SERVER_METADATA
    )

    az_request = client.authorization_request(
        scope="openid",
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
        request, use_dummy_server_metadata=USE_DUMMY_SERVER_METADATA
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

    print(az_response)
    token = client.authorization_code(
        az_response,
    )
    print(token)

    return HttpResponse(f"Good so far", status=200)
    token_response = client.authorization_code_token_request(
        az_response.code, code_verifier=code_verifier
    )

    request.session["user"] = token_response.id_token_claims

    # Clean up temporary authentication data
    del request.session["helseid_state"]
    del request.session["helseid_nonce"]
    del request.session["helseid_code_verifier"]

    return redirect("home")


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
