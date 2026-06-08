"""
Auth Mixin for User Management
Handles login, logout, and registration with JWT tokens
"""
import logging
from typing import Any, cast
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework_simplejwt.tokens import RefreshToken
from user_management.models import User
from helper.auth_decorators import rate_limit, captcha_guard

logger = logging.getLogger('user_management')


class AuthMixin:
    """Mixin to handle authentication (login, logout, register) with JWT"""
    
    @action(detail=False, methods=['post'], authentication_classes=[], permission_classes=[])
    # @rate_limit(limit=10, window=900, prefix='login', scope='ip')
    # @captcha_guard()
    def login(self, request: Request) -> Response:
        logger.debug("login running")
        """
        Login user and return JWT tokens with profile
        
        Request body:
            {
                "email": "user@example.com",
                "password": "password123"
            }
            
        Returns:
            {
                "access": "jwt_access_token",
                "refresh": "jwt_refresh_token",
                "user": {...user_profile...},
                "permissions": [...]
            }
        """
        email = request.data.get('email')  # type: ignore
        password = request.data.get('password')  # type: ignore
        
        logger.debug(f"login - received email: {email}")
        
        if not email or not password:
            logger.debug("login - email or password missing")
            return Response(
                {'error': 'email and password required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate using email - find user by email then check password
        logger.debug(f"login - attempting to find user with email={email}")
        try:
            user = User.objects.get(email=email)
            logger.debug(f"login - user found by email: {user.username}")
        except User.DoesNotExist:
            logger.debug(f"login - user not found with email: {email}")
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check password
        logger.debug("login - checking password")
        if not user.check_password(password):
            logger.debug("login - password incorrect")
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user = cast(User, user)
        logger.debug(f"login - user found: {user.email}, is_active: {user.is_active}")
        if not user.is_active:
            logger.debug("login - user is not active")
            return Response(
                {'error': 'Account is inactive'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Get serializer for user data
        from ...serializers import UserSerializer  # type: ignore
        user_serializer = UserSerializer(user)
        
        logger.debug(f"login - success for user: {user.email}")
        # Create response with tokens in body for localStorage
        response = Response(
            {
                'user': user_serializer.data,
                'permissions': self._get_user_permissions(user),
                'access': str(refresh.access_token),  # Include token in response body
                'refresh': str(refresh),  # Include refresh token too
            },
            status=status.HTTP_200_OK
        )
        
        # Set httpOnly cookies for tokens
        # DON'T set domain on localhost - let browser handle it
        response.set_cookie(
            key='access_token',
            value=str(refresh.access_token),
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=5 * 60,  # 5 minutes
            path='/',
        )
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=7 * 24 * 60 * 60,  # 7 days
            path='/',
        )
        
        return response
    
    @action(detail=False, methods=['post'], authentication_classes=[], permission_classes=[])
    def logout(self, request: Request) -> Response:
        """
        Logout user - clears authentication cookies
        No auth required - endpoint is idempotent
        """
        # Create response
        response = Response(
            {'status': 'Successfully logged out'},
            status=status.HTTP_200_OK
        )
        
        # Delete cookies by setting max_age to 0
        # Don't specify domain to allow all subdomains
        response.delete_cookie('access_token', path='/', samesite='Lax')
        response.delete_cookie('refresh_token', path='/', samesite='Lax')
        
        return response
    
    @action(detail=False, methods=['post'], authentication_classes=[], permission_classes=[])
    # @rate_limit(limit=5, window=3600, prefix='register', scope='ip')  # Disabled for testing
    # @captcha_guard()  # Disabled for testing
    def register(self, request: Request) -> Response:
        """
        Register new user
        
        Request body:
            {
                "email": "user@example.com",
                "username": "username",
                "password": "password123",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+1234567890"
            }
        """
        from ...serializers import UserSerializer  # type: ignore
        
        email = request.data.get('email')  # type: ignore
        username = request.data.get('username')  # type: ignore
        password = request.data.get('password')  # type: ignore
        
        if not email or not username or not password:
            return Response(
                {'error': 'email, username, and password required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user exists
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'Email already registered'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already taken'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user with password hashing
        try:
            user = User.objects.create_user(
                email=email,
                username=username,
                password=password,
                first_name=request.data.get('first_name', ''),  # type: ignore
                last_name=request.data.get('last_name', ''),  # type: ignore
                phone_number=request.data.get('phone_number', ''),  # type: ignore
            )
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            from ...serializers import UserSerializer  # type: ignore
            
            # Create response with tokens in body for localStorage
            response = Response(
                {
                    'user': UserSerializer(user).data,
                    'access': str(refresh.access_token),  # Include token in response body
                    'refresh': str(refresh),  # Include refresh token too
                },
                status=status.HTTP_201_CREATED
            )
            
            # Set httpOnly cookies for tokens
            response.set_cookie(
                key='access_token',
                value=str(refresh.access_token),
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=5 * 60,
                path='/',
            )
            response.set_cookie(
                key='refresh_token',
                value=str(refresh),
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=7 * 24 * 60 * 60,
                path='/',
            )
            
            return response
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    

    @action(detail=False, methods=['post'], authentication_classes=[], permission_classes=[])
    def refresh(self, request: Request) -> Response:
        """
        Refresh JWT access token using refresh token
        
        Request body:
            {
                "refresh": "jwt_refresh_token"
            }
            
        Returns:
            {
                "access": "new_jwt_access_token",
                "refresh": "new_jwt_refresh_token"  (rotated)
            }
        """
        refresh_token = request.data.get('refresh')  # type: ignore
        
        if not refresh_token:
            return Response(
                {'error': 'refresh token required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            token = RefreshToken(refresh_token)  # type: ignore
            
            # Create response with new tokens in body for localStorage
            response = Response(
                {
                    'access': str(token.access_token),  # New access token
                    'refresh': str(token),  # New/rotated refresh token
                },
                status=status.HTTP_200_OK
            )
            
            # Set new tokens in httpOnly cookies
            response.set_cookie(
                key='access_token',
                value=str(token.access_token),
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=5 * 60,
                path='/',
            )
            response.set_cookie(
                key='refresh_token',
                value=str(token),
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=7 * 24 * 60 * 60,
                path='/',
            )
            
            return response
        except Exception as e:
            return Response(
                {'error': f'Invalid refresh token: {str(e)}'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    def _get_user_permissions(self, user: User) -> list:
        """
        Get user permissions
        
        Args:
            user: User instance
            
        Returns:
            List of permission codenames
        """
        user = cast(User, user)
        if user.is_superuser:
            return ['*']  # Superuser has all permissions
        
        if user.is_staff:
            return list(user.user_permissions.values_list('codename', flat=True))
        
        return []
