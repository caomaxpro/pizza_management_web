#!/usr/bin/env python
"""Test FormData price update"""
import sys
import os
sys.path.insert(0, '/home/cao-le/Web Projects/pizza_admin_web/backend/backend_dj')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_dj.settings')

import django
django.setup()

from user_management.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from pizza_management.ingredient.model import Ingredient
import requests

BASE_URL = "http://127.0.0.1:8000"

def get_auth_token():
    """Get JWT token for testing"""
    user = User.objects.filter(username='admin').first()
    if not user:
        print("❌ Admin user not found")
        return None
    
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)

def test_formdata_update():
    """Test updating with FormData (like from browser)"""
    token = get_auth_token()
    if not token:
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
    }
    
    ingredient = Ingredient.objects.first()
    if not ingredient:
        print("❌ No ingredients found")
        return
    
    print(f"\n📋 Initial State:")
    print(f"   ID: {ingredient.id}")
    print(f"   Price (DB): {ingredient.price}")
    print(f"   Original Price (DB): {ingredient.original_price}")
    
    # Test 1: FormData with string values
    print(f"\n📝 Test 1: FormData with string values")
    new_price = ingredient.price + 10.0
    new_original_price = ingredient.original_price + 10.0 if ingredient.original_price else None
    
    form_data = {
        'price': str(new_price),
        'original_price': str(new_original_price) if new_original_price else ''
    }
    print(f"   FormData: {form_data}")
    
    response = requests.patch(
        f"{BASE_URL}/api/pizza/ingredients/{ingredient.id}/",
        data=form_data,
        headers=headers
    )
    
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json().get('error') or 'Success'}")
    
    ingredient.refresh_from_db()
    print(f"   Price (DB): {ingredient.price}")
    print(f"   Original Price (DB): {ingredient.original_price}")
    
    # Test 2: FormData with list values (what browser FormData actually sends)
    print(f"\n📝 Test 2: FormData with list values (actual FormData format)")
    new_price = ingredient.price + 20.0
    new_original_price = ingredient.original_price + 20.0 if ingredient.original_price else None
    
    form_data = {
        'price': [str(new_price)],  # FormData sends as list
        'original_price': [str(new_original_price)] if new_original_price else ['']
    }
    print(f"   FormData: {form_data}")
    
    response = requests.patch(
        f"{BASE_URL}/api/pizza/ingredients/{ingredient.id}/",
        data=form_data,
        headers=headers
    )
    
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json().get('error') or 'Success'}")
    
    ingredient.refresh_from_db()
    print(f"   Price (DB): {ingredient.price}")
    print(f"   Original Price (DB): {ingredient.original_price}")

if __name__ == '__main__':
    test_formdata_update()
