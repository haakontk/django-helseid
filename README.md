# django-helseid

Django application for authenticating users with HelseID

## Installation

**⚠️ WARNING: This project is currently under development and is NOT production-ready. It is intended for demonstration and testing purposes only. Do not use in a production environment without thorough security review and further development. ⚠️**



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
       'CLIENT_SECRET': { ... }, # JWK dict
       'SCOPE': ['openid', 'profile', ...],
       'SERVER_METADATA_URL': "https://helseid-sts.test.nhn.no/.well-known/openid-configuration",
   }
   ```
