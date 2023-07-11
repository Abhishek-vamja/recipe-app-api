"""
Test for ingredients APIs.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from recipe.serializers import IngredientSerializer
from core.models import Ingredient


INGREDIENT_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    """Create and return detail url"""
    return reverse('recipe:ingredient-detail',args=[ingredient_id])

def create_user(email='user@gmail.com',password='pass123'):
    """Create and return new user."""
    return get_user_model().objects.create_user(email=email,password=password)


class PublicIngredientAPI(TestCase):
    """Test unauthenticated API request."""

    def setUp(self):
        self.client = APIClient()
    
    def test_auth_required(self):
        """Test auth is required for retrieving ingredients."""
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code,status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientAPI(TestCase):
    """Test authenticated API request."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)
    
    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients."""
        Ingredient.objects.create(user=self.user,name='Ingredient1')
        Ingredient.objects.create(user=self.user,name='Ingredient2')

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients,many=True)

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(res.data,serializer.data)

    def test_limited_to_user(self):
        """Test list of ingredients is limited to authenticated user."""
        user2 = create_user(email='user2@gmail.com')
        Ingredient.objects.create(user=user2,name='Pepper')
        ingredient = Ingredient.objects.create(user=self.user,name='Salt')

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(len(res.data),1)
        self.assertEqual(res.data[0]['name'],ingredient.name)
        self.assertEqual(res.data[0]['id'],ingredient.id)
    
    def test_update_ingredients(self):
        """Test updating a ingredients."""
        ingredient = Ingredient.objects.create(user=self.user,name='Tomato')

        payload = {'name':'Onion'}
        url = detail_url(ingredient.id)
        res = self.client.patch(url,payload)

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        ingredient.refresh_from_db()

        self.assertEqual(ingredient.name,payload['name'])
    
    def test_delete_ingredients(self):
        """Test deleting a ingredients."""
        ingredient = Ingredient.objects.create(user=self.user,name='Paper')

        url = detail_url(ingredient.id)

        res = self.client.delete(url)
        self.assertEqual(res.status_code,status.HTTP_204_NO_CONTENT)

        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())