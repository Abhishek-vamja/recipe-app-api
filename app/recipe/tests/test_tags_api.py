"""
Tests for tags APIs.
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag,Recipe

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')

def detail_url(tag_id):
    """Create and return detail url."""
    return reverse('recipe:tag-detail',args=[tag_id])

def create_user(email='user@gmail.com',password='pas123'):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email,password)


class PublicTagsApiTest(TestCase):
    """Test unauthenticated API request."""

    def setUp(self):
        self.client = APIClient()
    
    def test_auth_required(self):
        """Test auth is required for retrieving tags."""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code,status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTest(TestCase):
    """Test authenticated API request."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)
    
    def test_retrieve_tags(self):
        """Test retrieving a list of tags."""
        Tag.objects.create(user=self.user,name='Vegan')
        Tag.objects.create(user=self.user,name='Dessert')

        res = self.client.get(TAGS_URL)
 
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags,many=True)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(res.data,serializer.data)
    
    def test_limited_to_user(self):
        """Test list of tags is limited to authenticated user."""
        user2 = create_user(email='user2@gmail.com')
        Tag.objects.create(user=user2,name='Fruity')
        tag = Tag.objects.create(user=self.user,name='Comfort Food')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(len(res.data),1)
        self.assertEqual(res.data[0]['name'],tag.name)
        self.assertEqual(res.data[0]['id'],tag.id)
    
    def test_update_tag(self):
        """Test updating tags."""
        tag = Tag.objects.create(user=self.user,name='After Dinner')
        
        payload={'name':'Dessert'}
        url = detail_url(tag.id)
        res = self.client.patch(url,payload)

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        tag.refresh_from_db()
        
        self.assertEqual(tag.name,payload['name'])
    
    def test_delete_tag(self):
        """Test deleting a tag."""
        tag = Tag.objects.create(user=self.user,name='BreakFast')

        url = detail_url(tag.id)

        res = self.client.delete(url)
        self.assertEqual(res.status_code,status.HTTP_204_NO_CONTENT)
        
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())
    
    def test_filtered_tags_assigned_to_recipes(self):
        """Test listing tags to those assigned to recipes."""
        tag1 = Tag.objects.create(user=self.user,name='BreakFast')
        tag2 = Tag.objects.create(user=self.user,name='Lunch')
        recipe = Recipe.objects.create(
            title='Green Eggs On Tost',
            time_minutes=10,
            price=Decimal('2.50'),
            user=self.user
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL,{'assigned_only':1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)

        self.assertIn(s1.data,res.data)
        self.assertNotIn(s2.data,res.data)
    
    def test_filtered_tags_unique(self):
        """Test filtered tags returns a unique list."""
        tag = Tag.objects.create(user=self.user,name='BreakFast')
        Tag.objects.create(user=self.user,name='Dinner')
        r1 = Recipe.objects.create(
            title='Pancake',
            time_minutes=5,
            price=Decimal('5.00'),
            user=self.user
        )
        r2 = Recipe.objects.create(
            title='Porridge',
            time_minutes=3,
            price=Decimal('2.00'),
            user=self.user
        )
        r1.tags.add(tag)
        r2.tags.add(tag)

        res = self.client.get(TAGS_URL,{'assigned_only':1})

        self.assertEqual(len(res.data),1)