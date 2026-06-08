# # pizza_management/item/tests.py
# from django.test import TestCase
# from rest_framework.test import APITestCase, APIClient
# from rest_framework import status
# from pathlib import Path
# import json
# import tempfile
# from PIL import Image
# import io

# from pizza_management.item.model import Item
# from pizza_management.ingredient.model import Ingredient
# from django.conf import settings
# from django.test import override_settings


# class ItemTestDataSetup(APITestCase):
#     """Base setup for item tests with required ingredients"""
    
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         # Create required ingredients
#         cls.dough = Ingredient.objects.create(
#             name="Regular Dough",
#             type="dough",
#             price=2.00,
#             is_active=True
#         )
#         cls.sauce = Ingredient.objects.create(
#             name="Tomato Sauce",
#             type="sauce",
#             price=1.50,
#             is_active=True
#         )
#         cls.cheese = Ingredient.objects.create(
#             name="Mozzarella",
#             type="cheese",
#             price=2.50,
#             is_active=True
#         )
#         cls.topping1 = Ingredient.objects.create(
#             name="Pepperoni",
#             type="topping",
#             price=1.50,
#             is_active=True
#         )
#         cls.topping2 = Ingredient.objects.create(
#             name="Mushroom",
#             type="topping",
#             price=1.00,
#             is_active=True
#         )


# class ItemCreateTestCase(ItemTestDataSetup):
#     """Test cases for Item create endpoint"""
    
#     def setUp(self):
#         self.client = APIClient()
#         self.url = '/api/items/'
    
#     def create_test_image(self, name="test.png"):
#         """Create a temporary test image"""
#         file = io.BytesIO()
#         img = Image.new('RGB', (100, 100), color='red')
#         img.save(file, format='PNG')
#         file.seek(0)
#         file.name = name
#         return file
    
#     @override_settings(DEBUG=True)
#     def test_create_item_without_image(self):
#         """Test creating item without image"""
#         data = {
#             'name': 'Margherita',
#             'price': 12.99,
#             'description': 'Classic pizza',
#             'category': 'pizza',
#             'type': 'pizza',
#             'dough': self.dough.id,
#             'sauce': self.sauce.id,
#             'cheese': self.cheese.id,
#             'is_active': 'true',
#             'stock_quantity': 50
#         }
#         response = self.client.post(self.url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(response.json()['name'], 'Margherita')
#         self.assertEqual(Item.objects.count(), 1)
    
#     @override_settings(DEBUG=True)
#     def test_create_item_with_image(self):
#         """Test creating item with image"""
#         data = {
#             'name': 'Pepperoni Pizza',
#             'price': 14.99,
#             'description': 'Loaded with pepperoni',
#             'category': 'pizza',
#             'type': 'pizza',
#             'dough': self.dough.id,
#             'sauce': self.sauce.id,
#             'cheese': self.cheese.id,
#             'image_file': self.create_test_image(),
#             'is_active': 'true',
#             'stock_quantity': 40
#         }
#         response = self.client.post(self.url, data, format='multipart')
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         response_data = response.json()
#         self.assertIsNotNone(response_data.get('image_url'))
#         self.assertEqual(Item.objects.count(), 1)
    
#     @override_settings(DEBUG=True)
#     def test_create_item_with_multiple_toppings(self):
#         """Test creating item with multiple toppings"""
#         data = {
#             'name': 'Supreme',
#             'price': 16.99,
#             'description': 'Everything included',
#             'category': 'pizza',
#             'type': 'pizza',
#             'dough': self.dough.id,
#             'sauce': self.sauce.id,
#             'cheese': self.cheese.id,
#             'toppings': [self.topping1.id, self.topping2.id],
#             'is_active': 'true',
#             'stock_quantity': 30
#         }
#         response = self.client.post(self.url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         item = Item.objects.get(name='Supreme')
#         self.assertEqual(item.toppings.count(), 2)
    
#     def test_create_item_invalid_ingredient_id(self):
#         """Test creating item with invalid ingredient ID"""
#         data = {
#             'name': 'Invalid Pizza',
#             'price': 12.99,
#             'category': 'pizza',
#             'type': 'pizza',
#             'dough': 9999,  # Non-existent
#             'sauce': self.sauce.id,
#             'cheese': self.cheese.id,
#             'is_active': 'true'
#         }
#         response = self.client.post(self.url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("error", response.json())
    
#     def test_create_item_missing_required_fields(self):
#         """Test creating item without required fields"""
#         data = {
#             'name': 'Incomplete Pizza',
#             # Missing price, category, type
#         }
#         response = self.client.post(self.url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertEqual(Item.objects.count(), 0)


# class ItemUpdateTestCase(ItemTestDataSetup):
#     """Test cases for Item update endpoint"""
    
#     def setUp(self):
#         self.client = APIClient()
#         self.url = '/api/items/'
        
#         self.item = Item.objects.create(
#             name='Original Pizza',
#             price=12.99,
#             category='pizza',
#             type='pizza',
#             stock_quantity=50
#         )
#         self.item.dough = self.dough
#         self.item.sauce = self.sauce
#         self.item.cheese = self.cheese
#         self.item.save()
#         self.item.toppings.add(self.topping1)
    
#     @override_settings(DEBUG=True)
#     def test_update_item_name(self):
#         """Test updating item name"""
#         data = {'name': 'Updated Pizza'}
#         response = self.client.patch(f'{self.url}{self.item.id}/', data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.item.refresh_from_db()
#         self.assertEqual(self.item.name, 'Updated Pizza')
    
#     @override_settings(DEBUG=True)
#     def test_update_item_price(self):
#         """Test updating item price"""
#         data = {'price': 15.99}
#         response = self.client.patch(f'{self.url}{self.item.id}/', data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.item.refresh_from_db()
#         self.assertEqual(self.item.price, 15.99)
    
#     @override_settings(DEBUG=True)
#     def test_update_item_with_new_topping(self):
#         """Test updating item with new topping"""
#         new_topping = Ingredient.objects.create(
#             name='Bacon',
#             type='topping',
#             price=1.75,
#             is_active=True
#         )
        
#         data = {'toppings': [new_topping.id]}
#         response = self.client.patch(f'{self.url}{self.item.id}/', data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
        
#         self.item.refresh_from_db()
#         topping_ids = list(self.item.toppings.values_list('id', flat=True))
#         self.assertEqual(topping_ids, [new_topping.id])
    
#     def test_update_nonexistent_item(self):
#         """Test updating non-existent item"""
#         data = {'name': 'Non-existent'}
#         response = self.client.patch(f'{self.url}9999/', data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
#     @override_settings(DEBUG=True)
#     def test_update_many_items(self):
#         """Test batch update multiple items"""
#         item2 = Item.objects.create(
#             name='Pizza 2',
#             price=10.99,
#             category='pizza',
#             type='pizza'
#         )
        
#         data = [
#             {'id': self.item.id, 'price': 15.99},
#             {'id': item2.id, 'price': 11.99}
#         ]
#         response = self.client.post(
#             f'{self.url}update-many/',
#             data,
#             format='json'
#         )
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
        
#         self.item.refresh_from_db()
#         item2.refresh_from_db()
#         self.assertEqual(self.item.price, 15.99)
#         self.assertEqual(item2.price, 11.99)
    
#     @override_settings(DEBUG=True)
#     def test_adjust_prices_positive_percentage(self):
#         """Test price adjustment by positive percentage"""
#         response = self.client.patch(
#             f'{self.url}adjust-prices/',
#             {'percent': 10},
#             format='json'
#         )
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.json()['updated_count'], 1)
        
#         self.item.refresh_from_db()
#         expected_price = 12.99 * 1.10
#         self.assertAlmostEqual(self.item.price, round(expected_price, 2), places=2)
    
#     @override_settings(DEBUG=True)
#     def test_adjust_prices_negative_percentage(self):
#         """Test price adjustment by negative percentage (discount)"""
#         response = self.client.patch(
#             f'{self.url}adjust-prices/',
#             {'percent': -10},
#             format='json'
#         )
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
        
#         self.item.refresh_from_db()
#         expected_price = 12.99 * 0.90
#         self.assertAlmostEqual(self.item.price, round(expected_price, 2), places=2)


# class ItemDeleteTestCase(ItemTestDataSetup):
#     """Test cases for Item delete endpoint"""
    
#     def setUp(self):
#         self.client = APIClient()
#         self.url = '/api/items/'
        
#         self.items = [
#             Item.objects.create(name='Pizza 1', price=10.99, category='pizza', type='pizza'),
#             Item.objects.create(name='Pizza 2', price=11.99, category='pizza', type='pizza'),
#             Item.objects.create(name='Pizza 3', price=12.99, category='pizza', type='pizza'),
#         ]
    
#     @override_settings(DEBUG=True)
#     def test_delete_single_item(self):
#         """Test deleting single item"""
#         url = f'{self.url}{self.items[0].id}/'
#         response = self.client.delete(url)
#         self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
#         self.assertEqual(Item.objects.count(), 2)
    
#     @override_settings(DEBUG=True)
#     def test_delete_many_items(self):
#         """Test deleting multiple items"""
#         url = f'{self.url}delete-many/'
#         data = {'ids': [self.items[0].id, self.items[1].id]}
#         response = self.client.post(url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.json()['deleted_count'], 2)
#         self.assertEqual(Item.objects.count(), 1)
    
#     def test_delete_many_empty_ids(self):
#         """Test delete-many with empty IDs list"""
#         url = f'{self.url}delete-many/'
#         data = {'ids': []}
#         response = self.client.post(url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertEqual(Item.objects.count(), 3)
    
#     @override_settings(DEBUG=True)
#     def test_delete_all_items(self):
#         """Test deleting all items"""
#         url = f'{self.url}delete-all/'
#         response = self.client.post(url, {})
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.json()['deleted_count'], 3)
#         self.assertEqual(Item.objects.count(), 0)
    
#     def test_delete_nonexistent_item(self):
#         """Test deleting non-existent item"""
#         url = f'{self.url}9999/'
#         response = self.client.delete(url)
#         self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# class ItemListTestCase(ItemTestDataSetup):
#     """Test cases for Item list endpoint"""
    
#     def setUp(self):
#         self.client = APIClient()
        
#         self.item1 = Item.objects.create(
#             name='Margherita',
#             price=12.99,
#             category='pizza',
#             type='pizza',
#             is_active=True,
#             stock_quantity=50
#         )
#         self.item1.dough = self.dough
#         self.item1.sauce = self.sauce
#         self.item1.cheese = self.cheese
#         self.item1.save()
#         self.item1.toppings.add(self.topping1)
        
#         self.item2 = Item.objects.create(
#             name='Pepperoni',
#             price=14.99,
#             category='pizza',
#             type='pizza',
#             is_active=True,
#             stock_quantity=40
#         )
#         self.item2.dough = self.dough
#         self.item2.sauce = self.sauce
#         self.item2.cheese = self.cheese
#         self.item2.save()
#         self.item2.toppings.add(self.topping1, self.topping2)
        
#         self.item3 = Item.objects.create(
#             name='Inactive Pizza',
#             price=10.99,
#             category='pizza',
#             type='pizza',
#             is_active=False,
#             stock_quantity=20
#         )
        
#         self.url = '/api/items/'
    
#     @override_settings(DEBUG=True)
#     def test_list_all_items(self):
#         """Test listing all items"""
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.json()), 3)
    
#     @override_settings(DEBUG=True)
#     def test_retrieve_single_item(self):
#         """Test retrieving single item with nested ingredients"""
#         response = self.client.get(f'{self.url}{self.item1.id}/')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         data = response.json()
#         self.assertEqual(data['name'], 'Margherita')
#         self.assertEqual(data['price'], 12.99)
#         # Check nested ingredient details
#         self.assertEqual(data['dough']['id'], self.dough.id)
#         self.assertEqual(data['dough']['name'], 'Regular Dough')
#         self.assertEqual(len(data['toppings']), 1)
    
#     def test_retrieve_nonexistent_item(self):
#         """Test retrieving non-existent item"""
#         response = self.client.get(f'{self.url}9999/')
#         self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
#     @override_settings(DEBUG=True)
#     def test_filter_by_name(self):
#         """Test filtering items by name"""
#         response = self.client.get(f'{self.url}?name=Margherita')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.json()), 1)
#         # self.assertEqual(data[0]['name'], 'Margherita')
    
#     @override_settings(DEBUG=True)
#     def test_filter_by_category(self):
#         """Test filtering items by category"""
#         response = self.client.get(f'{self.url}?category=pizza')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.json()), 3)
    
#     @override_settings(DEBUG=True)
#     def test_filter_by_is_active_true(self):
#         """Test filtering by is_active=true"""
#         response = self.client.get(f'{self.url}?is_active=true')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.json()), 2)
#         names = [item['name'] for item in response.json()]
#         self.assertNotIn('Inactive Pizza', names)
    
#     @override_settings(DEBUG=True)
#     def test_filter_by_price_range(self):
#         """Test filter_items endpoint with price range"""
#         response = self.client.get(f'{self.url}filter-items/?price_min=13&price_max=15')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.json()), 1)
#         self.assertEqual(response.json()[0]['name'], 'Pepperoni')
    
#     @override_settings(DEBUG=True)
#     def test_retrieve_shows_nested_toppings(self):
#         """Test that retrieve shows full topping details"""
#         response = self.client.get(f'{self.url}{self.item2.id}/')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         toppings = response.json()['toppings']
#         self.assertEqual(len(toppings), 2)
#         topping_names = [t['name'] for t in toppings]
#         self.assertIn('Pepperoni', topping_names)
#         self.assertIn('Mushroom', topping_names)


# class ItemImportJsonTestCase(ItemTestDataSetup):
#     """Test cases for Item import-json endpoint"""
    
#     @override_settings(DEBUG=True)
#     def setUp(self):
#         self.client = APIClient()
#         self.url = '/api/items/import-json/'
        
#         # Create temporary directory for test images
#         self.temp_dir = tempfile.mkdtemp()
#         self.test_image_path = Path(self.temp_dir) / 'test.png'
        
#         # Create test image
#         img = Image.new('RGB', (100, 100), color='blue')
#         img.save(self.test_image_path)
    
#     @override_settings(DEBUG=True)
#     def test_import_json_with_valid_data(self):
#         """Test importing valid JSON data"""
#         items_data = {
#             "items": [
#                 {
#                     "name": "Imported Pizza 1",
#                     "price": 11.99,
#                     "category": "pizza",
#                     "type": "pizza",
#                     "dough": self.dough.id,
#                     "sauce": self.sauce.id,
#                     "cheese": self.cheese.id,
#                     "is_active": True,
#                     "stock_quantity": 25
#                 },
#                 {
#                     "name": "Imported Pizza 2",
#                     "price": 13.99,
#                     "category": "pizza",
#                     "type": "pizza",
#                     "dough": self.dough.id,
#                     "sauce": self.sauce.id,
#                     "cheese": self.cheese.id,
#                     "is_active": True,
#                     "stock_quantity": 30
#                 }
#             ]
#         }
        
#         json_file = io.BytesIO(json.dumps(items_data).encode())
#         json_file.name = 'items.json'
        
#         data = {'json_file': json_file}
#         response = self.client.post(self.url, data, format='multipart')
        
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         response_data = response.json()
#         self.assertEqual(len(response_data['created']), 2)
#         self.assertEqual(Item.objects.count(), 2)
    
#     @override_settings(DEBUG=True)
#     def test_import_json_with_invalid_ingredient_id(self):
#         """Test importing JSON with invalid ingredient ID"""
#         items_data = {
#             "items": [
#                 {
#                     "name": "Invalid Item",
#                     "price": 12.99,
#                     "category": "pizza",
#                     "type": "pizza",
#                     "dough": 9999,  # Non-existent
#                     "sauce": self.sauce.id,
#                     "cheese": self.cheese.id,
#                     "is_active": True
#                 }
#             ]
#         }
        
#         json_file = io.BytesIO(json.dumps(items_data).encode())
#         json_file.name = 'items.json'
        
#         data = {'json_file': json_file}
#         response = self.client.post(self.url, data, format='multipart')
        
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         response_data = response.json()
#         self.assertEqual(len(response_data['errors']), 1)
#         self.assertEqual(Item.objects.count(), 0)
    
#     @override_settings(DEBUG=True)
#     def test_import_json_with_duplicate_id(self):
#         """Test importing JSON with duplicate IDs (should skip)"""
#         # Create initial item
#         item = Item.objects.create(
#             id=100,
#             name='Original Item',
#             price=10.99,
#             category='pizza',
#             type='pizza'
#         )
        
#         items_data = {
#             "items": [
#                 {
#                     "id": 100,
#                     "name": "Should Skip",
#                     "price": 15.99,
#                     "category": "pizza",
#                     "type": "pizza",
#                     "dough": self.dough.id,
#                     "sauce": self.sauce.id,
#                     "cheese": self.cheese.id
#                 }
#             ]
#         }
        
#         json_file = io.BytesIO(json.dumps(items_data).encode())
#         json_file.name = 'items.json'
        
#         data = {'json_file': json_file}
#         response = self.client.post(self.url, data, format='multipart')
        
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         response_data = response.json()
#         self.assertEqual(len(response_data['skipped']), 1)
        
#         # Verify original data unchanged
#         item.refresh_from_db()
#         self.assertEqual(item.name, 'Original Item')
    
#     def test_import_json_empty_list(self):
#         """Test importing empty items list"""
#         items_data = {"items": []}
        
#         json_file = io.BytesIO(json.dumps(items_data).encode())
#         json_file.name = 'items.json'
        
#         data = {'json_file': json_file}
#         response = self.client.post(self.url, data, format='multipart')
        
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         response_data = response.json()
#         self.assertEqual(len(response_data['created']), 0)
    
#     def tearDown(self):
#         """Clean up temporary files"""
#         import shutil
#         shutil.rmtree(self.temp_dir, ignore_errors=True)


# class ItemModelTestCase(ItemTestDataSetup, TestCase):
#     """Test cases for Item model"""
    
#     def test_item_string_representation(self):
#         """Test item __str__ method"""
#         item = Item(name='Test Pizza', price=12.99, type='pizza')
#         self.assertEqual(str(item), 'Test Pizza')
    
#     def test_item_default_values(self):
#         """Test item default values"""
#         item = Item.objects.create(
#             name='Test Item',
#             price=10.99,
#             category='pizza',
#             type='pizza'
#         )
#         self.assertTrue(item.is_active)
#         self.assertEqual(item.stock_quantity, 0)
#         self.assertIsNone(item.image_url)
#         self.assertIsNone(item.piece_image_url)
    
#     def test_item_with_all_relationships(self):
#         """Test item with all FK and M2M relationships"""
#         item = Item.objects.create(
#             name='Complete Pizza',
#             price=15.99,
#             category='pizza',
#             type='pizza'
#         )
#         item.dough = self.dough
#         item.sauce = self.sauce
#         item.cheese = self.cheese
#         item.save()
#         item.toppings.add(self.topping1, self.topping2)
        
#         # self.assertEqual(item.dough.name, 'Regular Dough')
#         # self.assertEqual(item.sauce.name, 'Tomato Sauce')
#         self.assertEqual(item.toppings.count(), 2)
    
#     def test_item_m2m_operations(self):
#         """Test M2M operations on item"""
#         item = Item.objects.create(
#             name='Test M2M',
#             price=12.99,
#             category='pizza',
#             type='pizza'
#         )
        
#         # Add toppings
#         item.toppings.add(self.topping1)
#         self.assertEqual(item.toppings.count(), 1)
        
#         # Add more toppings
#         item.toppings.add(self.topping2)
#         self.assertEqual(item.toppings.count(), 2)
        
#         # Remove one topping
#         item.toppings.remove(self.topping1)
#         self.assertEqual(item.toppings.count(), 1)
        
#         # Clear all toppings
#         item.toppings.clear()
#         self.assertEqual(item.toppings.count(), 0)