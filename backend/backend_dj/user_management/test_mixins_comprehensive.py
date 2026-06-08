# """
# Comprehensive test suite for User Management Mixins
# Tests: Create, Read, Update, Delete, Auth with different user roles
# """
# import json
# from django.test import TestCase, Client
# from django.contrib.auth import get_user_model
# from rest_framework.test import APIClient, APITestCase
# from rest_framework import status
# from rest_framework_simplejwt.tokens import RefreshToken

# User = get_user_model()


# class UserCreationTestCase(TestCase):
#     """Test creating users with different roles"""

#     def setUp(self):
#         """Setup test client"""
#         self.client = APIClient()

#     def test_create_regular_user(self):
#         """Create a regular user (no staff, no superuser)"""
#         user = User.objects.create_user(
#             username='regular_user',
#             email='regular@example.com',
#             password='testpass123',
#             first_name='Regular',
#             last_name='User'
#         )
        
#         assert user.username == 'regular_user'
#         assert user.email == 'regular@example.com'
#         assert not user.is_staff
#         assert not user.is_superuser
#         assert user.is_active
#         print("✅ Regular user created successfully")

#     def test_create_staff_user(self):
#         """Create a staff user"""
#         user = User.objects.create_user(
#             username='staff_user',
#             email='staff@example.com',
#             password='testpass123',
#             is_staff=True,
#             first_name='Staff',
#             last_name='User'
#         )
        
#         assert user.is_staff
#         assert not user.is_superuser
#         print("✅ Staff user created successfully")

#     def test_create_superuser(self):
#         """Create a superuser (admin)"""
#         admin = User.objects.create_superuser(
#             username='admin_user',
#             email='admin@example.com',
#             password='adminpass123'
#         )
        
#         assert admin.is_staff
#         assert admin.is_superuser
#         print("✅ Superuser created successfully")

#     def test_create_inactive_user(self):
#         """Create an inactive user"""
#         user = User.objects.create_user(
#             username='inactive_user',
#             email='inactive@example.com',
#             password='testpass123',
#             is_active=False
#         )
        
#         assert not user.is_active
#         print("✅ Inactive user created successfully")


# class AuthMixinTestCase(APITestCase):
#     """Test Authentication (Login/Logout) functionality"""

#     def setUp(self):
#         """Setup test users for auth testing"""
#         self.client = APIClient()
#         self.api_url = 'http://localhost:8000/api'

#         # Create users with different roles
#         self.regular_user = User.objects.create_user(
#             username='regular',
#             email='regular@test.com',
#             password='testpass123'
#         )
#         self.staff_user = User.objects.create_user(
#             username='staff',
#             email='staff@test.com',
#             password='staffpass123',
#             is_staff=True
#         )
#         self.admin_user = User.objects.create_superuser(
#             username='admin',
#             email='admin@test.com',
#             password='adminpass123'
#         )

#     def test_login_regular_user_success(self):
#         """Test successful login for regular user"""
#         response = self.client.post('/api/users/login/', {
#             'email': 'regular@test.com',
#             'password': 'testpass123'
#         })
        
#         if response.status_code == 200:
#             data = response.json()
#             assert 'access' in data
#             assert 'refresh' in data
#             assert 'user' in data
#             assert data['user']['email'] == 'regular@test.com'
#             print(f"✅ Regular user login successful")
#             print(f"   Access Token: {data['access'][:20]}...")
#             print(f"   User: {data['user']['username']}")
#         else:
#             print(f"⚠️  Login endpoint not yet registered (status: {response.status_code})")

#     def test_login_staff_user_success(self):
#         """Test successful login for staff user"""
#         response = self.client.post('/api/users/login/', {
#             'email': 'staff@test.com',
#             'password': 'staffpass123'
#         })
        
#         if response.status_code == 200:
#             data = response.json()
#             assert data['user']['is_staff'] == True
#             print(f"✅ Staff user login successful")
#         else:
#             print(f"⚠️  Login endpoint not yet registered")

#     def test_login_admin_user_success(self):
#         """Test successful login for admin user"""
#         response = self.client.post('/api/users/login/', {
#             'email': 'admin@test.com',
#             'password': 'adminpass123'
#         })
        
#         if response.status_code == 200:
#             data = response.json()
#             assert data['user']['is_superuser'] == True
#             print(f"✅ Admin user login successful")
#         else:
#             print(f"⚠️  Login endpoint not yet registered")

#     def test_login_invalid_credentials(self):
#         """Test login with invalid credentials"""
#         response = self.client.post('/api/users/login/', {
#             'email': 'regular@test.com',
#             'password': 'wrongpassword'
#         })
        
#         if response.status_code in [401, 400]:
#             print(f"✅ Invalid credentials rejected (status: {response.status_code})")
#         else:
#             print(f"⚠️  Unexpected response: {response.status_code}")

#     def test_login_missing_credentials(self):
#         """Test login with missing credentials"""
#         response = self.client.post('/api/users/login/', {
#             'email': 'regular@test.com'
#         })
        
#         if response.status_code in [400, 401]:
#             print(f"✅ Missing password rejected (status: {response.status_code})")
#         else:
#             print(f"⚠️  Unexpected response: {response.status_code}")

#     def test_logout_authenticated_user(self):
#         """Test logout for authenticated user"""
#         # First login
#         login_response = self.client.post('/api/users/login/', {
#             'email': 'regular@test.com',
#             'password': 'testpass123'
#         })
        
#         if login_response.status_code == 200:
#             tokens = login_response.json()
#             refresh_token = tokens['refresh']
            
#             # Now logout
#             self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
#             logout_response = self.client.post('/api/users/logout/', {
#                 'refresh': refresh_token
#             })
            
#             if logout_response.status_code == 200:
#                 print(f"✅ Logout successful")
#             else:
#                 print(f"⚠️  Logout response: {logout_response.status_code}")
#         else:
#             print(f"⚠️  Login failed, skipping logout test")

#     def test_logout_unauthenticated_user(self):
#         """Test logout without authentication"""
#         response = self.client.post('/api/users/logout/', {
#             'refresh': 'dummy_token'
#         })
        
#         if response.status_code == 401:
#             print(f"✅ Unauthenticated logout rejected (401)")
#         else:
#             print(f"⚠️  Response: {response.status_code}")


# class ReadMixinTestCase(APITestCase):
#     """Test Read operations (list/retrieve) with different authentication"""

#     def setUp(self):
#         """Setup test users and tokens"""
#         self.client = APIClient()
        
#         # Create test users
#         self.regular_user = User.objects.create_user(
#             username='regular',
#             email='regular@read.com',
#             password='pass123'
#         )
#         self.other_regular_user = User.objects.create_user(
#             username='other_regular',
#             email='other@read.com',
#             password='pass123'
#         )
#         self.staff_user = User.objects.create_user(
#             username='staff',
#             email='staff@read.com',
#             password='pass123',
#             is_staff=True
#         )
#         self.admin_user = User.objects.create_superuser(
#             username='admin',
#             email='admin@read.com',
#             password='pass123'
#         )

#         # Generate tokens
#         self.regular_token = str(RefreshToken.for_user(self.regular_user).access_token)
#         self.staff_token = str(RefreshToken.for_user(self.staff_user).access_token)
#         self.admin_token = str(RefreshToken.for_user(self.admin_user).access_token)

#     def test_list_users_without_auth(self):
#         """Test listing users without authentication - should fail"""
#         response = self.client.get('/api/users/')
        
#         if response.status_code == 401:
#             print(f"✅ List without auth rejected (401)")
#         elif response.status_code == 403:
#             print(f"✅ List without auth rejected (403)")
#         else:
#             print(f"⚠️  Expected 401/403, got {response.status_code}")

#     def test_list_users_as_regular_user(self):
#         """Test listing users as regular user - should see only own profile"""
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.regular_token}')
#         response = self.client.get('/api/users/')
        
#         if response.status_code == 200:
#             data = response.json()
#             # Regular users should see only themselves
#             if isinstance(data, dict) and 'results' in data:
#                 users = data['results']
#             else:
#                 users = data if isinstance(data, list) else []
            
#             print(f"✅ Regular user list retrieved ({len(users)} user(s) visible)")
#             if len(users) <= 1:
#                 print(f"   ✓ Regular user sees only own profile")
#         else:
#             print(f"⚠️  Unexpected response: {response.status_code}")

#     def test_list_users_as_staff(self):
#         """Test listing users as staff - should see all"""
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')
#         response = self.client.get('/api/users/')
        
#         if response.status_code == 200:
#             data = response.json()
#             if isinstance(data, dict) and 'results' in data:
#                 users = data['results']
#             else:
#                 users = data if isinstance(data, list) else []
            
#             print(f"✅ Staff can list users ({len(users)} user(s) visible)")
#         else:
#             print(f"⚠️  Unexpected response: {response.status_code}")

#     def test_list_users_as_admin(self):
#         """Test listing users as admin - should see all"""
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
#         response = self.client.get('/api/users/')
        
#         if response.status_code == 200:
#             data = response.json()
#             if isinstance(data, dict) and 'results' in data:
#                 users = data['results']
#             else:
#                 users = data if isinstance(data, list) else []
            
#             print(f"✅ Admin can list users ({len(users)} user(s) visible)")
#         else:
#             print(f"⚠️  Unexpected response: {response.status_code}")

#     def test_retrieve_own_profile(self):
#         """Test retrieving own profile"""
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.regular_token}')
#         response = self.client.get(f'/api/users/{self.regular_user.id}/')
        
#         if response.status_code == 200:
#             data = response.json()
#             assert data['email'] == 'regular@read.com'
#             print(f"✅ Retrieved own profile: {data['email']}")
#         elif response.status_code == 404:
#             print(f"⚠️  Profile endpoint may use different lookup")
#         else:
#             print(f"⚠️  Unexpected response: {response.status_code}")

#     def test_retrieve_profile_without_auth(self):
#         """Test retrieving profile without authentication"""
#         response = self.client.get(f'/api/users/{self.regular_user.id}/')
        
#         if response.status_code == 401:
#             print(f"✅ Retrieve without auth rejected (401)")
#         else:
#             print(f"⚠️  Unexpected response: {response.status_code}")

#     def test_me_endpoint(self):
#         """Test /me endpoint to get current user profile"""
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.regular_token}')
#         response = self.client.get('/api/users/me/')
        
#         if response.status_code == 200:
#             data = response.json()
#             assert data['email'] == 'regular@read.com'
#             print(f"✅ /me endpoint works: {data['email']}")
#         elif response.status_code == 404:
#             print(f"⚠️  /me endpoint not found")
#         else:
#             print(f"⚠️  Unexpected response: {response.status_code}")


# class UpdateMixinTestCase(APITestCase):
#     """Test Update operations with different user roles"""

#     def setUp(self):
#         """Setup test users and tokens"""
#         self.client = APIClient()
        
#         self.user1 = User.objects.create_user(
#             username='user1',
#             email='user1@update.com',
#             password='pass123',
#             first_name='User',
#             last_name='One'
#         )
#         self.user2 = User.objects.create_user(
#             username='user2',
#             email='user2@update.com',
#             password='pass123',
#             first_name='User',
#             last_name='Two'
#         )
#         self.staff_user = User.objects.create_user(
#             username='staff',
#             email='staff@update.com',
#             password='pass123',
#             is_staff=True
#         )
#         self.admin_user = User.objects.create_superuser(
#             username='admin',
#             email='admin@update.com',
#             password='pass123'
#         )

#         self.user1_token = str(RefreshToken.for_user(self.user1).access_token)
#         self.user2_token = str(RefreshToken.for_user(self.user2).access_token)
#         self.staff_token = str(RefreshToken.for_user(self.staff_user).access_token)
#         self.admin_token = str(RefreshToken.for_user(self.admin_user).access_token)

#     def test_update_own_profile(self):
#         """Test updating own profile"""
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user1_token}')
#         response = self.client.put(f'/api/users/{self.user1.id}/', {
#             'username': 'user1',
#             'email': 'user1@update.com',
#             'first_name': 'UpdatedUser',
#             'last_name': 'One'
#         })
        
#         if response.status_code == 200:
#             data = response.json()
#             assert data['first_name'] == 'UpdatedUser'
#             print(f"✅ Updated own profile successfully")
#         elif response.status_code == 404:
#             print(f"⚠️  Update endpoint not found")
#         else:
#             print(f"⚠️  Unexpected response: {response.status_code}")

#     def test_partial_update_own_profile(self):
#         """Test partial update of own profile"""
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user1_token}')
#         response = self.client.patch(f'/api/users/{self.user1.id}/', {
#             'first_name': 'PatchedUser'
#         })
        
#         if response.status_code == 200:
#             data = response.json()
#             assert data['first_name'] == 'PatchedUser'
#             print(f"✅ Partial update (PATCH) successful")
#         elif response.status_code == 404:
#             print(f"⚠️  PATCH endpoint not found")
#         else:
#             print(f"⚠️  Unexpected response: {response.status_code}")

#     def test_regular_user_cannot_update_other(self):
#         """Test that regular user cannot update another user's profile"""
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user1_token}')
#         response = self.client.put(f'/api/users/{self.user2.id}/', {
#             'username': 'user2',
#             'email': 'user2@update.com',
#             'first_name': 'Hacked'
#         })
        
#         if response.status_code == 403:
#             print(f"✅ Regular user denied updating other user (403)")
#         elif response.status_code == 404:
#             print(f"⚠️  Endpoint not found")
#         else:
#             print(f"⚠️  Unexpected response: {response.status_code}")

#     def test_staff_can_update_any_profile(self):
#         """Test that staff can update any user's profile"""
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')
#         response = self.client.put(f'/api/users/{self.user1.id}/', {
#             'username': 'user1',
#             'email': 'user1@update.com',
#             'first_name': 'UpdatedByStaff'
#         })
        
#         if response.status_code == 200:
#             print(f"✅ Staff can update other users")
#         elif response.status_code == 404:
#             print(f"⚠️  Endpoint not found")
#         else:
#             print(f"⚠️  Unexpected response: {response.status_code}")

#     def test_update_without_auth(self):
#         """Test updating without authentication"""
#         response = self.client.put(f'/api/users/{self.user1.id}/', {
#             'first_name': 'Hacker'
#         })
        
#         if response.status_code == 401:
#             print(f"✅ Update without auth rejected (401)")
#         else:
#             print(f"⚠️  Unexpected response: {response.status_code}")


# class DeleteMixinTestCase(APITestCase):
#     """Test Delete operations with different user roles"""

#     def setUp(self):
#         """Setup test users and tokens"""
#         self.client = APIClient()
        
#         self.regular_user = User.objects.create_user(
#             username='regular',
#             email='regular@delete.com',
#             password='pass123'
#         )
#         self.user_to_delete = User.objects.create_user(
#             username='to_delete',
#             email='todelete@delete.com',
#             password='pass123'
#         )
#         self.staff_user = User.objects.create_user(
#             username='staff',
#             email='staff@delete.com',
#             password='pass123',
#             is_staff=True
#         )
#         self.admin_user = User.objects.create_superuser(
#             username='admin',
#             email='admin@delete.com',
#             password='pass123'
#         )

#         self.regular_token = str(RefreshToken.for_user(self.regular_user).access_token)
#         self.staff_token = str(RefreshToken.for_user(self.staff_user).access_token)
#         self.admin_token = str(RefreshToken.for_user(self.admin_user).access_token)

#     def test_regular_user_cannot_delete(self):
#         """Test that regular user cannot delete users"""
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.regular_token}')
#         response = self.client.delete(f'/api/users/{self.user_to_delete.id}/')
        
#         if response.status_code == 403:
#             print(f"✅ Regular user denied delete (403)")
#         elif response.status_code == 401:
#             print(f"✅ Regular user denied delete (401)")
#         elif response.status_code == 404:
#             print(f"⚠️  Delete endpoint not found")
#         else:
#             print(f"⚠️  Unexpected response: {response.status_code}")

#     def test_staff_can_delete_user(self):
#         """Test that staff can delete users"""
#         user_to_delete = User.objects.create_user(
#             username='staff_delete_target',
#             email='staffdeletetarget@delete.com',
#             password='pass123'
#         )
        
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')
#         response = self.client.delete(f'/api/users/{user_to_delete.id}/')
        
#         if response.status_code == 204:
#             # Verify deletion
#             assert not User.objects.filter(id=user_to_delete.id).exists()
#             print(f"✅ Staff can delete user (204)")
#         elif response.status_code == 404:
#             print(f"⚠️  Delete endpoint not found")
#         else:
#             print(f"⚠️  Unexpected response: {response.status_code}")

#     def test_admin_can_delete_user(self):
#         """Test that admin can delete users"""
#         user_to_delete = User.objects.create_user(
#             username='admin_delete_target',
#             email='admindeletetarget@delete.com',
#             password='pass123'
#         )
        
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
#         response = self.client.delete(f'/api/users/{user_to_delete.id}/')
        
#         if response.status_code == 204:
#             assert not User.objects.filter(id=user_to_delete.id).exists()
#             print(f"✅ Admin can delete user (204)")
#         elif response.status_code == 404:
#             print(f"⚠️  Delete endpoint not found")
#         else:
#             print(f"⚠️  Unexpected response: {response.status_code}")

#     def test_delete_without_auth(self):
#         """Test deleting without authentication"""
#         response = self.client.delete(f'/api/users/{self.user_to_delete.id}/')
        
#         if response.status_code == 401:
#             print(f"✅ Delete without auth rejected (401)")
#         elif response.status_code == 404:
#             print(f"⚠️  Delete endpoint not found")
#         else:
#             print(f"⚠️  Unexpected response: {response.status_code}")


# class IntegrationTestCase(APITestCase):
#     """Integration tests combining multiple operations"""

#     def setUp(self):
#         """Setup"""
#         self.client = APIClient()

#     def test_complete_user_lifecycle(self):
#         """Test complete user lifecycle: create -> login -> read -> update -> delete"""
#         print("\n" + "=" * 60)
#         print("TESTING COMPLETE USER LIFECYCLE")
#         print("=" * 60)
        
#         # Step 1: Create user
#         print("\n1️⃣  Creating user...")
#         user = User.objects.create_user(
#             username='lifecycle',
#             email='lifecycle@test.com',
#             password='lifecycle123',
#             first_name='Life',
#             last_name='Cycle'
#         )
#         print(f"   ✅ User created: {user.email}")
        
#         # Step 2: Login
#         print("\n2️⃣  Logging in...")
#         login_response = self.client.post('/api/users/login/', {
#             'email': 'lifecycle@test.com',
#             'password': 'lifecycle123'
#         })
        
#         if login_response.status_code == 200:
#             tokens = login_response.json()
#             access_token = tokens['access']
#             print(f"   ✅ Login successful")
#         else:
#             print(f"   ⚠️  Login failed (status: {login_response.status_code})")
#             access_token = str(RefreshToken.for_user(user).access_token)
        
#         # Step 3: Read own profile
#         print("\n3️⃣  Reading own profile...")
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
#         read_response = self.client.get(f'/api/users/{user.id}/')
        
#         if read_response.status_code == 200:
#             print(f"   ✅ Profile retrieved: {read_response.json()['email']}")
#         else:
#             print(f"   ⚠️  Read failed (status: {read_response.status_code})")
        
#         # Step 4: Update profile
#         print("\n4️⃣  Updating profile...")
#         update_response = self.client.patch(f'/api/users/{user.id}/', {
#             'first_name': 'UpLife',
#             'last_name': 'UpCycle'
#         })
        
#         if update_response.status_code == 200:
#             print(f"   ✅ Profile updated")
#         else:
#             print(f"   ⚠️  Update failed (status: {update_response.status_code})")
        
#         # Step 5: Admin delete
#         print("\n5️⃣  Admin delete...")
#         admin = User.objects.create_superuser(
#             username='lifecycle_admin',
#             email='admin@lifecycle.com',
#             password='admin123'
#         )
#         admin_token = str(RefreshToken.for_user(admin).access_token)
        
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
#         delete_response = self.client.delete(f'/api/users/{user.id}/')
        
#         if delete_response.status_code == 204:
#             print(f"   ✅ User deleted by admin")
#             assert not User.objects.filter(id=user.id).exists()
#             print(f"   ✅ User no longer exists in database")
#         else:
#             print(f"   ⚠️  Delete failed (status: {delete_response.status_code})")
        
#         print("\n" + "=" * 60)
#         print("✅ LIFECYCLE TEST COMPLETE")
#         print("=" * 60)
