import json
from requests_oauth2client import OAuth2Client

from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import HttpResponse
from django.conf import settings





def home(request):
    user = request.session.get('user')
    if user:
        user = json.dumps(user)
    return render(request, 'helseid/home.html', context={'user': user})


def login(request):
    # Bygg redirect URLen til din callback view
    django_redirect_uri = request.build_absolute_uri(reverse('auth')) 


    oauth2client = OAuth2Client(
        token_endpoint="https://url.to.the/token_endpoint",
        client_id=settings.HELSEID_CLIENT_ID,
        client_secret=settings.HELSEID_CLIENT_SECRET,
    )
    print(django_redirect_uri)
    return HttpResponse("yay")


def auth(request):

    # Do auth stuff
    
    return redirect('home')