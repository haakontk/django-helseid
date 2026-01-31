from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import HelseIDProfile

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


    @override_settings(AUTHENTICATION_BACKENDS=['helseid.backends.HelseIDBackend'])
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
