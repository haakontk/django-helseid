import json
import logging
from requests_oauth2client.exceptions import OAuth2Error
from requests_oauth2client.dpop import DPoPKey

from django.conf import settings
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
import datetime
from .utils import get_helseid_client

logger = logging.getLogger(__name__)


def home(request):
    return render(request, "helseid/home.html")


def login(request):
    client = get_helseid_client(
        request
    )
    scope = " ".join(settings.HELSEID["SCOPE"])

    az_request = client.authorization_request(
        scope=scope,
        prompt='login',
    )

    # Save DPoP key to session — must reuse the same key at the token endpoint
    if az_request.dpop_key:
        request.session["helseid_dpop_key"] = az_request.dpop_key.private_key.to_dict()

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

        logger.error(f"Error during PAR request: {e}")
        logger.error(f"HelseID server response: {error_response}")
        return HttpResponse("Failed to initiate login.", status=500)


def auth(request):
    client = get_helseid_client(
        request
    )

    state = request.session.get("helseid_state")
    nonce = request.session.get("helseid_nonce")
    code_verifier = request.session.get("helseid_code_verifier")

    dpop_key = None
    dpop_key_dict = request.session.get("helseid_dpop_key")

    if dpop_key_dict:
        dpop_key = DPoPKey(private_key=dpop_key_dict)  # reconstruct from JWK dict


    if not state or not nonce or not code_verifier or not dpop_key:
        return HttpResponse("Missing authentication session data.", status=400)

    az_request = client.authorization_request(
        scope="openid", state=state, nonce=nonce, code_verifier=code_verifier, dpop_key=dpop_key,
    )

    az_response = az_request.validate_callback(request.build_absolute_uri())


    token = client.authorization_code(
        az_response,
        dpop_key=dpop_key,   
        validate=False, ## Needs to be set to true when DPOP token validation issue in requests_oauth2client is resolved
    )

    id_token = token.id_token

    # NEXT: VERIFY ID_TOKEN
    subject = id_token.subject
    auth_datetime = id_token.auth_datetime
    given_name = id_token.get_claim("given_name")
    family_name = id_token.get_claim("family_name")
    middle_name = id_token.get_claim("middle_name")
    hpr_number = id_token.get_claim("helseid://claims/hpr/hpr_number")

    logger.debug(f"Subject: {subject}")
    logger.debug(f"Given Name: {given_name}")
    logger.debug(f"Family Name: {family_name}")
    logger.debug(f"Middle Name: {middle_name}")
    logger.debug(f"HPR Number: {hpr_number}")
    logger.debug(f"Auth Datetime: {auth_datetime}")



    user = authenticate(request, id_token_payload=id_token)
    logger.debug(f"Authenticated user: {user}")


    if user:
        django_login(request, user)
        # Set session expiry to 2 hours from auth_datetime
        session_expiry = auth_datetime + datetime.timedelta(hours=2)
        request.session.set_expiry(session_expiry)

        # Clean up temporary authentication data
        del request.session["helseid_state"]
        del request.session["helseid_nonce"]
        del request.session["helseid_code_verifier"]

        return redirect(getattr(settings, "LOGIN_REDIRECT_URL", "/"))
    else:
        return HttpResponse("Authentication failed.", status=403)


def logout(request):
    # implement this later
    # client = get_helseid_client(request)
    # end_session_endpoint = client.server_metadata.get("end_session_endpoint")

    # 1. Clear the local Django session
    django_logout(request)

    # implement this later
    # 2. Redirect to HelseID to clear the SSO session
    # if end_session_endpoint:
    #     return redirect(end_session_endpoint)

    return redirect("/")
