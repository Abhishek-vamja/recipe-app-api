"""
Test for the user API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the public feature of the user API."""

    def setUp(self):
        self.client = APIClient()
    
    # TEST 12
    def test_create_user_success(self):
        """Test creating a user is successful."""
        payload = {
            'email':'test1@gmail.com',
            'password':'testpass123',
            'name':'Test Name'
        }

        res = self.client.post(CREATE_USER_URL,payload)

        self.assertEqual(res.status_code,status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password',res.data)
    
    # TEST 13
    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exist."""
        payload ={
            'email':'test1@gmail.com',
            'password':'testpass123',
            'name':'Test Name',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL,payload)

        self.assertEqual(res.status_code,status.HTTP_400_BAD_REQUEST)
    
    # TEST 14
    def test_password_to_short_error(self):
        """Test an error is returned if password less than 5 chars."""
        payload = {
            'email':'test1@gmail.com',
            'password':'pw',
            'name':'Test Name',
        }
        res = self.client.post(CREATE_USER_URL,payload)

        self.assertEqual(res.status_code,status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(email=payload['email']).exists()
        self.assertFalse(user_exists)

    # TEST 15
    def test_create_token_for_user(self):
        """Test generate token for valid credentials."""
        user_detail = {
            'name':'Tets Name',
            'email':'test@gmail.com',
            'password':'test-pass-123',
        }
        create_user(**user_detail)

        payload = {
            'email':user_detail['email'],
            'password':user_detail['password'],
        }
        res = self.client.post(TOKEN_URL,payload)

        self.assertIn('token',res.data)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
    
    # TEST 16
    def test_create_token_bad_credentials(self):
        """Test return error if credentials invalid"""
        create_user(email='test@gmail.com',password='goodpass')

        payload = {
            'email': 'test@gmail.com',
           'password': 'badpass'
        }
        res = self.client.post(TOKEN_URL,payload)

        self.assertNotIn('token',res.data)
        self.assertEqual(res.status_code,status.HTTP_400_BAD_REQUEST)
    
    # TEST 17
    def test_create_token_blank_password(self):
        """Test return error if password blank."""
        payload = {
            'email':'token@gmail.com',
            'password':''
        }
        res = self.client.post(TOKEN_URL,payload)

        self.assertNotIn('token',res.data)
        self.assertEqual(res.status_code,status.HTTP_400_BAD_REQUEST)
    
    # TEST 18
    def test_create_token_blank_email(self):
        """Test return error if email blank."""
        payload = {
            'email':'',
            'password':'goodpass'
        }
        res = self.client.post(TOKEN_URL,payload)

        self.assertNotIn('token',res.data)
        self.assertEqual(res.status_code,status.HTTP_400_BAD_REQUEST)
    
    # TEST 19
    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for user."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code,status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API request that required authentication."""

    def setUp(self):
        self.user=create_user(
            email='test@gmail.com',
            password='testpass123',
            name='Test Name',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    # TEST 20
    def test_retrieve_profile_success(self):
        """Tets retrieving profile for logged in user."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(res.data,{
            'name':self.user.name,
            'email':self.user.email,
        })
    
    # TEST 21
    def test_post_me_not_allowed(self):
        """Test POST is not allowed for me endpoint."""
        res = self.client.post(ME_URL,{})

        self.assertEqual(res.status_code,status.HTTP_405_METHOD_NOT_ALLOWED)
    
    # TEST 22
    def test_update_user_profile(self):
        """Test updating the user profile for the authenticated user."""
        payload = {
            'name':'updatename',
            'password':'newpass123',
        }

        res = self.client.patch(ME_URL,payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name,payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code,status.HTTP_200_OK)