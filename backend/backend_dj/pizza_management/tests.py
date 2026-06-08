# tests.py
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from pathlib import Path
import json
import tempfile
from PIL import Image
import io

from pizza_management.models import Ingredient
from django.conf import settings
from django.test import override_settings


class IngredientCreateTestCase(APITestCase):
    """Test cases for Ingredient create endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/ingredients/'
    
    def create_test_image(self, name="test.png"):
        """Create a temporary test image"""
        file = io.BytesIO()
        img = Image.new('RGB', (100, 100), color='red')
        img.save(file, format='PNG')
        file.seek(0)
        file.name = name
        return file
    
    def test_create_ingredient_without_image(self):
        """Test creating ingredient without image"""
        data = {
            'name': 'Pepperoni',
            'price': 2.50,
            'type': 'topping',
            'is_active': 'true'
        }
        response = self.client.post(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], 'Pepperoni')
        self.assertEqual(Ingredient.objects.count(), 1)
    
    def test_create_ingredient_with_image(self):
        """Test creating ingredient with image"""
        data = {
            'name': 'Mushroom',
            'price': 1.50,
            'type': 'topping',
            'image_file': self.create_test_image()
        }
        response = self.client.post(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        self.assertIsNotNone(response_data.get('image_url'))
        self.assertEqual(Ingredient.objects.count(), 1)
    
    def test_create_ingredient_invalid_type(self):
        """Test creating ingredient with invalid type"""
        data = {
            'name': 'Invalid',
            'price': 1.00,
            'type': 'invalid_type'
        }
        response = self.client.post(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Ingredient.objects.count(), 0)
    
    def test_create_ingredient_invalid_price(self):
        """Test creating ingredient with invalid price"""
        data = {
            'name': 'Invalid',
            'price': -5.00,
            'type': 'topping'
        }
        response = self.client.post(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Ingredient.objects.count(), 0)
    
    def test_create_ingredient_missing_required_fields(self):
        """Test creating ingredient without required fields"""
        data = {
            'name': 'Incomplete'
            # Missing price and type
        }
        response = self.client.post(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Ingredient.objects.count(), 0)
    
    def test_create_ingredient_sub_type_only_for_topping(self):
        """Test sub_type only allowed for topping"""
        data = {
            'name': 'Dough',
            'price': 2.00,
            'type': 'dough',
            'sub_type': 'thin'
        }
        response = self.client.post(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class IngredientUpdateTestCase(APITestCase):
    """Test cases for Ingredient update endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.ingredient = Ingredient.objects.create(
            name='Original',
            price=2.00,
            type='topping'
        )
        self.url = f'/api/ingredients/{self.ingredient.id}/'
    
    def test_update_ingredient_name(self):
        """Test updating ingredient name"""
        data = {'name': 'Updated Name'}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.name, 'Updated Name')
    
    def test_update_ingredient_price(self):
        """Test updating ingredient price"""
        data = {'price': 3.50}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.price, 3.50)
    
    def test_update_ingredient_is_active(self):
        """Test updating is_active status"""
        data = {'is_active': 'false'}
        response = self.client.patch(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ingredient.refresh_from_db()
        self.assertFalse(self.ingredient.is_active)
    
    def test_update_nonexistent_ingredient(self):
        """Test updating non-existent ingredient"""
        url = f'/api/ingredients/9999/'
        data = {'name': 'Updated'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class IngredientDeleteTestCase(APITestCase):
    """Test cases for Ingredient delete endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.ingredients = [
            Ingredient.objects.create(name='Ing1', price=1.00, type='topping'),
            Ingredient.objects.create(name='Ing2', price=2.00, type='sauce'),
            Ingredient.objects.create(name='Ing3', price=3.00, type='cheese'),
        ]
    
    def test_delete_single_ingredient(self):
        """Test deleting single ingredient"""
        url = f'/api/ingredients/{self.ingredients[0].id}/'
        response = self.client.delete(url)
        # HTTP 204 No Content - no response body
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Ingredient.objects.count(), 2)
    
    def test_delete_many_ingredients(self):
        """Test deleting multiple ingredients"""
        url = '/api/ingredients/delete-many/'
        data = {'ids': [self.ingredients[0].id, self.ingredients[1].id]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data['deleted_count'], 2)
        self.assertEqual(Ingredient.objects.count(), 1)
    
    def test_delete_many_no_ids(self):
        """Test delete-many without IDs"""
        url = '/api/ingredients/delete-many/'
        data = {'ids': []}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Ingredient.objects.count(), 3)
    
    def test_delete_many_empty_list(self):
        """Test delete-many with None ids"""
        url = '/api/ingredients/delete-many/'
        data = {}  # No 'ids' key
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Ingredient.objects.count(), 3)
    
    def test_delete_all_ingredients(self):
        """Test deleting all ingredients"""
        url = '/api/ingredients/delete-all/'
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data['deleted_count'], 3)
        self.assertEqual(Ingredient.objects.count(), 0)
    
    def test_delete_all_empty(self):
        """Test delete-all when already empty"""
        Ingredient.objects.all().delete()
        url = '/api/ingredients/delete-all/'
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data['deleted_count'], 0)


class IngredientListTestCase(APITestCase):
    """Test cases for Ingredient list endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.ingredient1 = Ingredient.objects.create(
            name='Pepperoni', 
            price=2.00, 
            type='topping', 
            is_active=True
        )
        self.ingredient2 = Ingredient.objects.create(
            name='Sausage', 
            price=2.00, 
            type='topping', 
            is_active=False
        )
        self.ingredient3 = Ingredient.objects.create(
            name='Tomato Sauce', 
            price=1.00, 
            type='sauce', 
            is_active=True
        )
        self.url = '/api/ingredients/'
    
    def test_list_all_ingredients(self):
        """Test listing all ingredients"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 3)
    
    def test_filter_by_name(self):
        """Test filtering by name"""
        response = self.client.get(f'{self.url}?name=Pepperoni')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Pepperoni')
    
    def test_filter_by_type(self):
        """Test filtering by type"""
        response = self.client.get(f'{self.url}?type=topping')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)
    
    def test_filter_by_is_active(self):
        """Test filtering by is_active"""
        response = self.client.get(f'{self.url}?is_active=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)
    
    def test_filter_by_is_active_false(self):
        """Test filtering by is_active=false"""
        response = self.client.get(f'{self.url}?is_active=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)
    
    def test_retrieve_single_ingredient(self):
        """Test retrieving single ingredient"""
        # Use existing ingredient from setUp instead of first()
        response = self.client.get(f'{self.url}{self.ingredient1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data['id'], self.ingredient1.id)
        self.assertEqual(response_data['name'], 'Pepperoni')


class IngredientImportJsonTestCase(APITestCase):
    """Test cases for Ingredient import-json endpoint"""
    
    # Override settings for test
    @override_settings(DEBUG=True)
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/ingredients/import-json/'
        
        # Create temporary directory for test images
        self.temp_dir = tempfile.mkdtemp()
        self.test_image_path = Path(self.temp_dir) / 'test.png'
        
        # Create test image
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(self.test_image_path)
        
    @override_settings(DEBUG=True)
    def test_import_json_from_real_file(self):
        """Test importing from actual ingredients.json file"""
        # Path to the actual ingredients.json
        json_file_path = Path(__file__).parent.parent / 'test' / 'ingredients.json'
    
        if not json_file_path.exists():
            self.skipTest(f"Test file not found at {json_file_path}")
    
        # Read the file
        with open(json_file_path, 'r') as f:
            json_data = f.read()
    
        json_file = io.BytesIO(json_data.encode())
        json_file.name = 'ingredients.json'
    
        data = {'json_file': json_file}
        response = self.client.post(self.url, data, format='multipart')
    
        # Should import successfully
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
    
        print(f"\n[Test Result] Created: {len(response_data['created'])}, Errors: {len(response_data['errors'])}")
        if response_data['errors']:
            for err in response_data['errors']:
                print(f"  Error: {err}")
    
        # Check that we got results
        self.assertIn('created', response_data)
        self.assertIn('errors', response_data)
    
        # Should have created items
        self.assertGreater(len(response_data['created']), 0, 
                           f"No items created. Errors: {response_data['errors']}")
    
        # Verify data is in database
        db_count = Ingredient.objects.count()
        self.assertEqual(db_count, len(response_data['created']),
                          f"DB count {db_count} != created count {len(response_data['created'])}")
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_import_json_with_valid_data(self):
        """Test importing valid JSON data"""
        ingredients_data = {
            "ingredients": [
                {
                    "name": "Bacon",
                    "price": 1.50,
                    "type": "topping"
                },
                {
                    "name": "Cheese",
                    "price": 2.00,
                    "type": "cheese"
                }
            ]
        }
        
        json_file = io.BytesIO(json.dumps(ingredients_data).encode())
        json_file.name = 'ingredients.json'
        
        data = {'json_file': json_file}
        response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(len(response_data['created']), 2)
        self.assertEqual(Ingredient.objects.count(), 2)
    
    def test_import_json_with_invalid_data(self):
        """Test importing JSON with invalid ingredient data"""
        ingredients_data = {
            "ingredients": [
                {
                    "name": "Invalid",
                    "price": -5.00,  # Invalid price
                    "type": "topping"
                }
            ]
        }
        
        json_file = io.BytesIO(json.dumps(ingredients_data).encode())
        json_file.name = 'ingredients.json'
        
        data = {'json_file': json_file}
        response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(len(response_data['errors']), 1)
        self.assertEqual(Ingredient.objects.count(), 0)
    
    def test_import_json_not_list(self):
        """Test importing JSON that's not a list"""
        ingredients_data = {"name": "Single Item"}
        
        json_file = io.BytesIO(json.dumps(ingredients_data).encode())
        json_file.name = 'ingredients.json'
        
        data = {'json_file': json_file}
        response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_import_json_empty_list(self):
        """Test importing empty ingredients list"""
        ingredients_data = {"ingredients": []}
        
        json_file = io.BytesIO(json.dumps(ingredients_data).encode())
        json_file.name = 'ingredients.json'
        
        data = {'json_file': json_file}
        response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(len(response_data['created']), 0)


class IngredientModelTestCase(TestCase):
    """Test cases for Ingredient model"""
    
    def test_ingredient_string_representation(self):
        """Test ingredient __str__ method"""
        ingredient = Ingredient(name='Pepperoni', price=2.00, type='topping')
        self.assertEqual(str(ingredient), 'Pepperoni (Topping)')
    
    def test_ingredient_clean_sub_type_validation(self):
        """Test sub_type validation in clean method"""
        from django.core.exceptions import ValidationError
        
        ingredient = Ingredient(
            name='Dough',
            price=2.00,
            type='dough',
            sub_type='thin'
        )
        
        with self.assertRaises(ValidationError):
            ingredient.clean()
    
    def test_ingredient_sub_type_allowed_for_topping(self):
        """Test sub_type is allowed for topping"""
        ingredient = Ingredient(
            name='Pepperoni',
            price=2.00,
            type='topping',
            sub_type='sliced'
        )
        # Should not raise
        ingredient.clean()
    
    def test_ingredient_default_values(self):
        """Test ingredient default values"""
        ingredient = Ingredient.objects.create(
            name='Test',
            price=1.00,
            type='sauce'
        )
        self.assertTrue(ingredient.is_active)
        self.assertIsNone(ingredient.description)
        self.assertIsNone(ingredient.image_url)