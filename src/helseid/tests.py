from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import HelseIDProfile
from .checks import check_helseid_settings

# Create your tests here.

class HelseIDAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser')
        self.dpop_key_dict = {
            'kty': 'EC',
            'crv': 'P-256',
            'x': 'V2YY4UJO2SAhehNmAjU2tKmzzL5msWBw1pFXxMALU1E',
            'y': '0YCPJbMbrzI9pJzdbgIfzeLZnVl88AJmnaXjDJI-fp0',
            'd': 'mo6HyZ1JmX6BmqfnfqiQhdRKN5z9X45q5RyNmKEciCk',
            'alg': 'ES256'
        }

    @override_settings(LOGIN_REDIRECT_URL='/')
    @patch('helseid.views.get_helseid_client')
    @patch('helseid.views.authenticate')
    def test_session_expiry_is_two_hours_from_auth_time(self, mock_authenticate, mock_get_client):
        # Mock the HelseID client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock authorization flow
        mock_az_request = MagicMock()
        mock_client.authorization_request.return_value = mock_az_request
        mock_az_request.validate_callback.return_value = MagicMock()
        
        mock_token = MagicMock()
        mock_client.authorization_code.return_value = mock_token
        
        mock_id_token = MagicMock()
        mock_token.id_token = mock_id_token
        
        # Setup ID Token data
        auth_time = datetime.now(timezone.utc)
        mock_id_token.auth_datetime = auth_time
        mock_id_token.subject = "test_subject"
        mock_id_token.get_claim.return_value = "test_value"

        # Mock authenticate to return the user
        # We must set the backend so login() works
        self.user.backend = 'django.contrib.auth.backends.ModelBackend'
        mock_authenticate.return_value = self.user

        # Setup session
        session = self.client.session
        session['helseid_state'] = 'state'
        session['helseid_nonce'] = 'nonce'
        session['helseid_code_verifier'] = 'verifier'
        session['helseid_dpop_key'] = self.dpop_key_dict
        session.save()

        # Perform request
        url = reverse('auth')
        response = self.client.get(url, {'code': 'code', 'state': 'state'})

        # Assert redirect to home
        self.assertRedirects(response, reverse('home'))

        # Verify authorization_code was called with validate=False and the dpop_key
        mock_client.authorization_code.assert_called_once()
        _, kwargs = mock_client.authorization_code.call_args
        self.assertFalse(kwargs.get('validate'), "Validation should be disabled to bypass library bug")

        # Verify session expiry
        expected_expiry = auth_time + timedelta(hours=2)
        actual_expiry = self.client.session.get_expiry_date()
        
        self.assertAlmostEqual(
            actual_expiry, 
            expected_expiry, 
            delta=timedelta(seconds=5),
            msg="Session expiry should be 2 hours from auth_datetime"
        )


    @override_settings(AUTHENTICATION_BACKENDS=['helseid.backends.HelseIDBackend'], LOGIN_REDIRECT_URL='/')
    @patch('helseid.views.get_helseid_client')
    def test_full_authentication_flow_creates_user_and_logs_in(self, mock_get_client):
        # Mock the HelseID client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock authorization flow objects
        mock_az_request = MagicMock()
        mock_client.authorization_request.return_value = mock_az_request
        mock_az_request.validate_callback.return_value = MagicMock()
        
        mock_token = MagicMock()
        mock_client.authorization_code.return_value = mock_token
        
        mock_id_token = MagicMock()
        mock_token.id_token = mock_id_token
        
        # Setup ID Token data
        mock_id_token.subject = "new_test_subject"
        mock_id_token.auth_datetime = datetime.now(timezone.utc)
        
        def get_claim_side_effect(claim):
            claims = {
                "given_name": "Test",
                "family_name": "User",
                "middle_name": None,
                "helseid://claims/hpr/hpr_number": "123456789"
            }
            return claims.get(claim)
            
        mock_id_token.get_claim.side_effect = get_claim_side_effect

        # Setup session
        session = self.client.session
        session['helseid_state'] = 'state'
        session['helseid_nonce'] = 'nonce'
        session['helseid_code_verifier'] = 'verifier'
        session['helseid_dpop_key'] = self.dpop_key_dict
        session.save()

        # Perform request
        url = reverse('auth')
        response = self.client.get(url, {'code': 'auth_code', 'state': 'state'})

        # Assertions
        self.assertRedirects(response, reverse('home'))
        
        # Check if user was created
        user_model = get_user_model()
        self.assertTrue(user_model.objects.filter(username="new_test_subject").exists())
        user = user_model.objects.get(username="new_test_subject")
        
        # Check if user is logged in (session contains user id)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

        # Check HelseIDProfile creation
        profile = HelseIDProfile.objects.get(user=user)
        self.assertEqual(profile.subject, "new_test_subject")
        self.assertEqual(profile.hpr_number, "123456789")

    @override_settings(LOGIN_REDIRECT_URL='/custom/dashboard/')
    @patch('helseid.views.get_helseid_client')
    @patch('helseid.views.authenticate')
    def test_custom_login_redirect_url(self, mock_authenticate, mock_get_client):
        # Mock the HelseID client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock authorization flow
        mock_az_request = MagicMock()
        mock_client.authorization_request.return_value = mock_az_request
        mock_az_request.validate_callback.return_value = MagicMock()
        
        mock_token = MagicMock()
        mock_client.authorization_code.return_value = mock_token
        
        mock_id_token = MagicMock()
        mock_token.id_token = mock_id_token
        
        # Setup ID Token data
        mock_id_token.auth_datetime = datetime.now(timezone.utc)
        mock_id_token.subject = "test_subject"
        mock_id_token.get_claim.return_value = "test_value"

        # Mock authenticate to return the user
        self.user.backend = 'django.contrib.auth.backends.ModelBackend'
        mock_authenticate.return_value = self.user

        # Setup session
        session = self.client.session
        session['helseid_state'] = 'state'
        session['helseid_nonce'] = 'nonce'
        session['helseid_code_verifier'] = 'verifier'
        session['helseid_dpop_key'] = self.dpop_key_dict
        session.save()

        # Perform request
        url = reverse('auth')
        response = self.client.get(url, {'code': 'code', 'state': 'state'})

        # Assert redirect to custom URL
        self.assertRedirects(response, '/custom/dashboard/', fetch_redirect_response=False)

    def test_logout_view_clears_session(self):
        self.client.force_login(self.user)
        self.assertIn('_auth_user_id', self.client.session)
        
        response = self.client.get(reverse('logout'))
        
        self.assertRedirects(response, reverse('home'))
        self.assertNotIn('_auth_user_id', self.client.session)

class HelseIDSystemCheckTests(TestCase):
    @override_settings(AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'])
    def test_helseid_backend_missing_check(self):
        errors = check_helseid_settings(None)
        self.assertTrue(any(e.id == 'helseid.E003' for e in errors))

    @override_settings(AUTHENTICATION_BACKENDS=['helseid.backends.HelseIDBackend'])
    def test_helseid_backend_present_check(self):
        errors = check_helseid_settings(None)
        self.assertFalse(any(e.id == 'helseid.E003' for e in errors))

    @override_settings(HELSEID={})
    def test_helseid_missing_required_keys(self):
        errors = check_helseid_settings(None)
        required_keys = ['CLIENT_ID', 'CLIENT_SECRET', 'SCOPE', 'SERVER_METADATA_URL']
        for key in required_keys:
            self.assertTrue(any(e.id == f'helseid.E002_{key}' for e in errors))

    @override_settings(HELSEID={
        'CLIENT_ID': 'test_id',
        'CLIENT_SECRET': 'test_secret',
        'SCOPE': 'test_scope',
        'SERVER_METADATA_URL': 'https://test.url'
    })
    def test_helseid_all_required_keys_present(self):
        errors = check_helseid_settings(None)
        self.assertFalse(any(e.id.startswith('helseid.E002') for e in errors))

    @override_settings()
    def test_helseid_setting_missing(self):
        from django.conf import settings
        if hasattr(settings, 'HELSEID'):
            del settings.HELSEID
        errors = check_helseid_settings(None)
        self.assertTrue(any(e.id == 'helseid.E001' for e in errors))

    @override_settings()
    def test_login_redirect_url_warning_missing(self):
        from django.conf import settings
        if hasattr(settings, 'LOGIN_REDIRECT_URL'):
            del settings.LOGIN_REDIRECT_URL
        errors = check_helseid_settings(None)
        self.assertTrue(any(e.id == 'helseid.W001' for e in errors))

    @override_settings(LOGIN_REDIRECT_URL='/dashboard')
    def test_login_redirect_url_warning_not_present_when_set(self):
        errors = check_helseid_settings(None)
        self.assertFalse(any(e.id == 'helseid.W001' for e in errors))
