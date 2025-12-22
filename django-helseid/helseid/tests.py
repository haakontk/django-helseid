from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

# Create your tests here.

class HelseIDAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser')

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
        session.save()

        # Perform request
        url = reverse('auth')
        response = self.client.get(url, {'code': 'code', 'state': 'state'})

        # Assert redirect to home
        self.assertRedirects(response, reverse('home'))
        
        # Verify session expiry
        expected_expiry = auth_time + timedelta(hours=2)
        actual_expiry = self.client.session.get_expiry_date()
        
        self.assertAlmostEqual(
            actual_expiry, 
            expected_expiry, 
            delta=timedelta(seconds=5),
            msg="Session expiry should be 2 hours from auth_datetime"
        )

    def test_middleware_redirects_unauthenticated_users(self):
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, reverse('login'))

    @patch('helseid.views.get_helseid_client')
    def test_middleware_allows_exempt_urls_for_unauthenticated_users(self, mock_get_client):
        # Mock the client for the login view to prevent external calls
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_par_response = MagicMock()
        mock_par_response.uri = "http://dummy.url/redirect"
        mock_client.pushed_authorization_request.return_value = mock_par_response

        with self.subTest("Login page should be accessible"):
            response = self.client.get(reverse('login'))
            # The middleware should allow access. The view itself will then redirect
            # to the HelseID provider. We check for a redirect (302) that is NOT
            # a redirect back to the login page itself (which would indicate a loop).
            self.assertEqual(response.status_code, 302)
            self.assertNotEqual(response.url, reverse('login'))

        with self.subTest("Auth callback should be accessible"):
            response = self.client.get(reverse('auth'))
            # The middleware should allow access. The view itself will then fail
            # because of missing session data, returning a 400 Bad Request.
            # This is correct; we just need to ensure it's not a 302 redirect to login.
            self.assertEqual(response.status_code, 400)
