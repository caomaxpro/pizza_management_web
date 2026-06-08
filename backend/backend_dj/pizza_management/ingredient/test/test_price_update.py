#!/usr/bin/env python
"""Test script to debug price update issue"""
import requests
import json
import os
import sys

# Add Django setup
sys.path.insert(0, '/home/cao-le/Web Projects/pizza_admin_web/backend/backend_dj')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_dj.settings')

import django
django.setup()

from user_management.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from pizza_management.ingredient.model import Ingredient

BASE_URL = "http://127.0.0.1:8000"

def get_auth_token():
    """Get JWT token for testing"""
    # Create or get admin user
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@test.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        user.set_password('admin123')
        user.save()
    
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)

def test_price_update():
    """Test updating ingredient price"""
    token = get_auth_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Get an ingredient to update
    ingredient = Ingredient.objects.first()
    if not ingredient:
        print("❌ No ingredients found")
        return
    
    print(f"\n📋 Initial State:")
    print(f"   ID: {ingredient.id}")
    print(f"   Name: {ingredient.name}")
    print(f"   Price (DB): {ingredient.price}")
    print(f"   Original Price (DB): {ingredient.original_price}")
    
    # Test 1: Update via API
    print(f"\n📝 Updating via API...")
    new_price = ingredient.price + 5.0
    new_original_price = ingredient.original_price + 5.0 if ingredient.original_price else None
    
    payload = {
        'price': new_price,
        'original_price': new_original_price
    }
    print(f"   Payload: {payload}")
    
    response = requests.patch(
        f"{BASE_URL}/api/pizza/ingredients/{ingredient.id}/",
        json=payload,
        headers=headers
    )
    
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    
    # Check in database immediately
    ingredient.refresh_from_db()
    print(f"\n✅ After API Update (from DB):")
    print(f"   Price (DB): {ingredient.price}")
    print(f"   Original Price (DB): {ingredient.original_price}")
    
    # Test 2: Fetch via API to check if serializer works
    print(f"\n🔍 Fetching via API...")
    response = requests.get(
        f"{BASE_URL}/api/pizza/ingredients/{ingredient.id}/",
        headers=headers
    )
    print(f"   Status: {response.status_code}")
    api_data = response.json()
    print(f"   API Price: {api_data.get('price')}")
    print(f"   API Original Price: {api_data.get('original_price')}")
    
    # Verify values match
    print(f"\n📊 Verification:")
    if ingredient.price == new_price:
        print(f"   ✅ Price updated correctly in DB")
    else:
        print(f"   ❌ Price NOT updated in DB (expected {new_price}, got {ingredient.price})")
    
    if api_data.get('price') == new_price:
        print(f"   ✅ Price returned correctly from API")
    else:
        print(f"   ❌ Price NOT returned correctly from API")

if __name__ == '__main__':
    test_price_update()
