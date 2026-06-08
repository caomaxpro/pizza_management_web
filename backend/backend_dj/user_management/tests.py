from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User


def _make_user(role='customer', password='pass1234!', **kwargs):
    """Create a test user with the given role."""
    defaults = dict(
        username=f'user_{role}_{id(kwargs)}',
        email=f'{role}_{id(kwargs)}@test.com',
        password=password,
    )
    defaults.update(kwargs)
    u = User.objects.create_user(**defaults)
    u.role = role
    u.is_active = True
    u.save()
    return u


def _bearer(user):
    """Return a dict with a valid JWT Authorization header for the given user."""
    token = str(RefreshToken.for_user(user).access_token)
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


class CreateMixinTests(TestCase):
    """Tests for user_management CreateMixin"""

    def setUp(self):
        self.client = APIClient()
        self.admin = _make_user('admin', username='admin1', email='admin1@test.com')
        self.manager = _make_user('manager', username='mgr1', email='mgr1@test.com')

    # ── POST /api/users/  (public customer registration) ──────────────────

    def test_register_customer_public(self):
        """Anyone can register as a customer (no auth required)."""
        resp = self.client.post('/api/users/', {
            'username': 'newcust', 'email': 'newcust@test.com',
            'password': 'strong_pass_1!',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data.get('role'), 'customer')

    def test_register_customer_role_forced(self):
        """Passing role=admin in body must still result in role=customer."""
        resp = self.client.post('/api/users/', {
            'username': 'hacker', 'email': 'hacker@test.com',
            'password': 'strong_pass_1!',
            'role': 'admin',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data.get('role'), 'customer')

    # ── POST /api/users/create-staff/  (admin/manager only) ───────────────

    def test_create_staff_requires_auth(self):
        """Without a JWT token the endpoint returns 401."""
        resp = self.client.post('/api/users/create-staff/', {
            'username': 'newstaff', 'email': 'ns@test.com',
            'password': 'strong_pass_1!', 'role': 'staff',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_staff_rejects_customer_role(self):
        """create-staff must reject role=customer."""
        resp = self.client.post('/api/users/create-staff/', {
            'username': 'cust2', 'email': 'c2@test.com',
            'password': 'strong_pass_1!', 'role': 'customer',
        }, format='json', **_bearer(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_staff_rejects_admin_role(self):
        """create-staff must reject role=admin."""
        resp = self.client.post('/api/users/create-staff/', {
            'username': 'admin2', 'email': 'a2@test.com',
            'password': 'strong_pass_1!', 'role': 'admin',
        }, format='json', **_bearer(self.admin))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_cannot_create_manager(self):
        """A manager cannot create another manager account."""
        resp = self.client.post('/api/users/create-staff/', {
            'username': 'mgr2', 'email': 'mgr2@test.com',
            'password': 'strong_pass_1!', 'role': 'manager',
        }, format='json', **_bearer(self.manager))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class UpdateMixinTests(TestCase):
    """Tests for user_management UpdateMixin"""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()  # reset throttle counters (pks repeat across test transactions)
        self.client = APIClient()
        self.admin = _make_user('admin', username='admin_u', email='admin_u@test.com')
        self.manager = _make_user('manager', username='mgr_u', email='mgr_u@test.com')
        self.target = _make_user('staff', username='target_u', email='target_u@test.com')

    # ── PATCH /api/users/<id>/assign-role/ ────────────────────────────────

    def test_assign_role_invalid_role_rejected(self):
        """assign-role must reject unknown roles."""
        resp = self.client.patch(
            f'/api/users/{self.target.pk}/assign-role/',
            {'role': 'supervillain'},
            format='json',
            **_bearer(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_manager_cannot_assign_admin_role(self):
        """Manager cannot promote a user to admin."""
        resp = self.client.patch(
            f'/api/users/{self.target.pk}/assign-role/',
            {'role': 'admin'},
            format='json',
            **_bearer(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_assign_role_success(self):
        """Admin can change a staff user's role to manager."""
        resp = self.client.patch(
            f'/api/users/{self.target.pk}/assign-role/',
            {'role': 'manager'},
            format='json',
            **_bearer(self.admin),
        )
        self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.target.refresh_from_db()
        self.assertEqual(self.target.role, 'manager')

    def test_assign_role_logs_change(self):
        """assign-role must create a RoleChangeLog entry."""
        from .models import RoleChangeLog
        self.client.patch(
            f'/api/users/{self.target.pk}/assign-role/',
            {'role': 'customer'},
            format='json',
            **_bearer(self.admin),
        )
        self.assertTrue(RoleChangeLog.objects.filter(target_user=self.target).exists())

    # ── POST /api/users/change-password/ ──────────────────────────────────

    def test_change_password_wrong_old_password(self):
        """change-password must reject an incorrect old password."""
        resp = self.client.post(
            '/api/users/change-password/',
            {'old_password': 'wrong!', 'new_password': 'new_secure_1!'},
            format='json',
            **_bearer(self.target),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_too_short(self):
        """change-password must reject a new password shorter than 8 chars."""
        resp = self.client.post(
            '/api/users/change-password/',
            {'old_password': 'pass1234!', 'new_password': 'abc'},
            format='json',
            **_bearer(self.target),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_missing_fields(self):
        """change-password must return 400 when fields are missing."""
        resp = self.client.post(
            '/api/users/change-password/',
            {},
            format='json',
            **_bearer(self.target),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_success(self):
        """change-password succeeds with correct old password and a valid new one."""
        resp = self.client.post(
            '/api/users/change-password/',
            {'old_password': 'pass1234!', 'new_password': 'NewSecure99!'},
            format='json',
            **_bearer(self.target),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.target.refresh_from_db()
        self.assertTrue(self.target.check_password('NewSecure99!'))
