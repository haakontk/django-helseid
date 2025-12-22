from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class HelseIDSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            exempt_paths = [
                reverse('login'),
                reverse('auth'),
                reverse('dummy_token_endpoint'),
            ]
            
            static_url = settings.STATIC_URL
            if not static_url.startswith('/'):
                static_url = f'/{static_url}'

            if (request.path_info not in exempt_paths and 
                not request.path_info.startswith(static_url) and 
                not request.path_info.startswith('/admin/')):
                return redirect('login')

        return self.get_response(request)