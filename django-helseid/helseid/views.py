import json
from django.shortcuts import redirect, render
from django.urls import reverse
from authlib.integrations.django_client import OAuth

# Registrer klienten basert på settings
oauth = OAuth()
oauth.register(
    name='helseid',
)

def home(request):
    user = request.session.get('user')
    if user:
        user = json.dumps(user)
    return render(request, 'helseid/home.html', context={'user': user})


def login(request):
    # Bygg redirect URLen til din callback view
    redirect_uri = request.build_absolute_uri(reverse('auth'))
    
    # Authlib håndterer her automatisk:
    # 1. Generering av PKCE challenge
    # 2. PAR (hvis aktivert i settings)
    # 3. Redirect til HelseID
    return oauth.helseid.authorize_redirect(request, redirect_uri)

def auth(request):
    # Dette er callbacken fra HelseID
    # Authlib vil nå:
    # 1. Validere 'state' og PKCE
    # 2. Lage en JWT signert med din private nøkkel (client_assertion)
    # 3. Bytte code mot access_token hos HelseID
    token = oauth.helseid.authorize_access_token(request, with_dpop=True)
    
    # Hent brukerinfo (parse ID-token)
    user_info = token.get('userinfo')
    
    # Lagre i session eller logg inn bruker i Django
    request.session['user'] = user_info
    
    return redirect('dashboard')