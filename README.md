# django-helseid

[![CI](https://github.com/haakontk/django-helseid/actions/workflows/ci.yml/badge.svg)](https://github.com/haakontk/django-helseid/actions/workflows/ci.yml)

Django application for authenticating users with HelseID

## Installation

**⚠️ WARNING: This project is currently under development and is NOT production-ready. It is intended for demonstration and testing purposes only. Do not use in a production environment without thorough security review and further development. ⚠️**

**Requirements:** Python 3.12+, Django 6.0+

1. Install the package:
   ```bash
   pip install django-helseid
   ```
   Or locally for development:
   ```bash
   uv pip install -e .
   ```

2. Add `helseid` to your `INSTALLED_APPS` in `settings.py`:
   ```python
   INSTALLED_APPS = [
       ...
       'helseid',
   ]
   ```

3. Add the authentication backend:
   ```python
   AUTHENTICATION_BACKENDS = [
       'django.contrib.auth.backends.ModelBackend',
       'helseid.backends.HelseIDBackend',
   ]
   ```

4. Configure `HELSEID` settings:
   ```python
   HELSEID = {
       'CLIENT_ID': 'your-client-id',
       'CLIENT_SECRET': { ... }, # JWK dict (private key)
       'SCOPE': ['openid', 'profile', ...],
       'SERVER_METADATA_URL': "https://helseid-sts.test.nhn.no/.well-known/openid-configuration",
       'LOGIN_REDIRECT_URL': '/',  # where to send users after login
   }
   ```

5. Include the URL configuration in your `urls.py`:
   ```python
   from django.urls import path, include

   urlpatterns = [
       ...
       path('', include('helseid.urls')),
   ]
   ```
   This registers the following routes:
   - `GET /login/` — initiates the HelseID authentication flow
   - `GET /authorize/` — handles the OAuth2 callback
   - `GET /logout/` — clears the local session
