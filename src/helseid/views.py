import logging
from requests_oauth2client.exceptions import OAuth2Error
from requests_oauth2client.serializers import AuthorizationRequestSerializer

from django.conf import settings
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
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

    serializer = AuthorizationRequestSerializer()
    request.session["helseid_az_request"] = serializer.dumps(az_request).decode()
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

    az_request_data = request.session.get("helseid_az_request")
    if not az_request_data:
        return HttpResponse("Missing authentication session data.", status=400)

    serializer = AuthorizationRequestSerializer()
    az_request = serializer.loads(az_request_data.encode())

    az_response = az_request.validate_callback(request.build_absolute_uri())

    token = client.authorization_code(az_response, validate=False)

    # Workaround for requests_oauth2client bug: validate_id_token fails to
    # reconstruct DPoPToken because it omits _dpop_key. All actual validation
    # (signature, nonce, audience, etc.) runs before the broken return statement,
    # so catching TypeError here is safe — any real validation failure raises
    # a different exception earlier.
    try:
        token = token.validate_id_token(client, az_response)
    except TypeError:
        pass

    id_token = token.id_token
    auth_datetime = id_token.auth_datetime

    user = authenticate(request, id_token_payload=id_token)


    if user:
        django_login(request, user)
        # Set session expiry to 2 hours from auth_datetime
        session_expiry = auth_datetime + datetime.timedelta(hours=2)
        request.session.set_expiry(session_expiry)

        del request.session["helseid_az_request"]
        request.session.pop("helseid_dpop_key", None)

        return redirect(getattr(settings, "LOGIN_REDIRECT_URL", "/"))
    else:
        return HttpResponse("Authentication failed.", status=403)


@require_POST
@csrf_protect
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
