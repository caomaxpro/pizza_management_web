"""
Custom Authentication Decorator for Token Validation and Refresh
Handles:
1. Access token validation (check if still valid)
2. If expired: refresh using refresh token (if valid)
3. User validation (check if exists and is active)
4. New access token attachment to response header
"""
import logging
import functools
from typing import Optional, Callable, Any
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from user_management.models import User

logger = logging.getLogger('user_management')


class TokenValidator:
    """Helper class for token validation and refresh logic"""
    
    jwt_auth = JWTAuthentication()
    
    @staticmethod
    def extract_token(request) -> Optional[str]:
        """
        Extract access token from cookies or Authorization header.
        Priority: cookies > Authorization header
        
        Returns:
            str: Raw token string or None
        """
        # Try cookies first (preferred)
        token = request.COOKIES.get('access_token')
        if token:
            logger.debug("[TokenValidator] Token found in cookies")
            return token
        
        # Fall back to Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            logger.debug("[TokenValidator] Token found in Authorization header")
            return auth_header[7:]  # Remove 'Bearer ' prefix
        
        logger.debug("[TokenValidator] No token found in cookies or Authorization header")
        return None
    
    @staticmethod
    def validate_token(token: str) -> tuple:
        """
        Validate access token.
        
        Returns:
            tuple: (validated_token, user) on success
            
        Raises:
            AuthenticationFailed: If token is invalid/expired
        """
        try:
            # get_validated_token expects bytes, not str
            token_bytes = token.encode() if isinstance(token, str) else token
            validated_token = TokenValidator.jwt_auth.get_validated_token(token_bytes)
            user = TokenValidator.jwt_auth.get_user(validated_token)
            logger.debug(f"[TokenValidator] Access token valid for user: {user.email}")
            return validated_token, user
        except (InvalidToken, TokenError) as e:
            logger.debug(f"[TokenValidator] Access token validation failed: {str(e)}")
            raise AuthenticationFailed(f"Invalid or expired access token: {str(e)}")
    
    @staticmethod
    def refresh_access_token(request) -> Optional[str]:
        """
        Attempt to refresh access token using refresh token.
        
        Returns:
            str: New access token string if refresh successful, None otherwise
        """
        refresh_token_raw = request.COOKIES.get('refresh_token')
        if not refresh_token_raw:
            logger.debug("[TokenValidator] No refresh token found in cookies")
            return None
        
        try:
            logger.debug("[TokenValidator] Attempting to refresh access token...")
            refresh_token = RefreshToken(refresh_token_raw)
            new_access_token = str(refresh_token.access_token)
            logger.debug("[TokenValidator] ✓ Access token refreshed successfully")
            return new_access_token
        except (InvalidToken, TokenError) as e:
            logger.error(f"[TokenValidator] Refresh token validation failed: {str(e)}")
            return None
    
    @staticmethod
    def validate_user(user: User) -> bool:
        """
        Validate if user is valid and active.
        
        Returns:
            bool: True if user is valid and active, False otherwise
        """
        if not user:
            logger.warning("[TokenValidator] User is None")
            return False
        
        if not user.is_active:
            logger.warning(f"[TokenValidator] User {user.email} is not active")
            return False
        
        logger.debug(f"[TokenValidator] User {user.email} is valid and active")
        return True
    
    @staticmethod
    def validate_admin_request(request) -> tuple:
        """
        Validate token + user + admin permission for ViewSet methods.
        
        This helper is designed for DRF ViewSet methods where decorators don't work well.
        
        Returns:
            tuple: (user, error_response) where:
                - user: Authenticated admin user (or None if error)
                - error_response: None if valid, else Response object (error response)
        
        Example:
            def list(self, request, *args, **kwargs):
                user, error_response = TokenValidator.validate_admin_request(request)
                if error_response:
                    return error_response
                # user is authenticated admin, continue with logic
                ...
        """
        from rest_framework.exceptions import AuthenticationFailed
        
        # Step 1: Extract token
        token = TokenValidator.extract_token(request)
        if not token:
            logger.warning(f"[validate_admin_request] No token for {request.path}")
            return None, Response(
                {'error': 'No token provided'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Step 2: Try validate access token
        try:
            validated_token, user = TokenValidator.validate_token(token)
        except AuthenticationFailed as e:
            # Token invalid, try refresh
            logger.debug("[validate_admin_request] Token invalid, attempting refresh...")
            new_token = TokenValidator.refresh_access_token(request)
            
            if not new_token:
                logger.error("[validate_admin_request] Token refresh failed")
                return None, Response(
                    {'error': 'Token expired and refresh failed'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            try:
                validated_token, user = TokenValidator.validate_token(new_token)
                setattr(request, 'new_access_token', new_token)
                logger.debug("[validate_admin_request] Token refreshed successfully")
            except AuthenticationFailed as refresh_e:
                logger.error(f"[validate_admin_request] New token validation failed: {str(refresh_e)}")
                return None, Response(
                    {'error': str(refresh_e)},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        # Step 3: Validate user active
        if not TokenValidator.validate_user(user):
            return None, Response(
                {'error': 'User is not valid or inactive'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Step 4: Check admin permission (is_staff)
        if not user.is_staff:
            logger.warning(f"[validate_admin_request] User {user.email} not admin")
            return None, Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        logger.debug(f"[validate_admin_request] Admin auth OK for {user.email}")
        return user, None


def require_token(view_func: Callable) -> Callable:
    """
    Decorator for token-based authentication on view functions.
    
    Flow:
    1. Extract and validate access token
    2. If valid: validate user and let view run
    3. If invalid/expired: try to refresh using refresh token
       - If refresh success: validate user and let view run (attach new token to response)
       - If refresh fails: return 401 error
    4. If user is not valid/active: return 403 error
    
    Usage:
        @require_token
        def my_view(request):
            user = request.user  # User is attached by decorator
            ...
    
    Returns:
        Response: View response with optional X-New-Access-Token header
        
    Raises:
        AuthenticationFailed: If token validation fails and refresh not possible
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs) -> Any:
        logger.debug(f"[require_token] Decorator called for {request.path}")
        
        # Step 1: Extract token
        token = TokenValidator.extract_token(request)
        if not token:
            logger.warning(f"[require_token] No token provided for {request.path}")
            raise AuthenticationFailed("No token provided")
        
        # Step 2: Try to validate access token
        try:
            validated_token, user = TokenValidator.validate_token(token)
        except AuthenticationFailed:
            # Step 3: Access token invalid, try to refresh
            logger.debug("[require_token] Access token invalid, attempting refresh...")
            new_token = TokenValidator.refresh_access_token(request)
            
            if not new_token:
                logger.error("[require_token] Token refresh failed")
                raise AuthenticationFailed("Token expired and refresh failed")
            
            # Validate the new token
            try:
                validated_token, user = TokenValidator.validate_token(new_token)
                # Store new token on request for response header
                setattr(request, 'new_access_token', new_token)
                logger.debug("[require_token] ✓ New access token will be attached to response")
            except AuthenticationFailed as e:
                logger.error(f"[require_token] New token validation failed: {str(e)}")
                raise
        
        # Step 4: Validate user (active, exists)
        if not TokenValidator.validate_user(user):
            logger.warning(f"[require_token] User validation failed")
            raise AuthenticationFailed("User is not valid or inactive")
        
        # Step 5: Attach user to request and call view
        request.user = user
        logger.debug(f"[require_token] ✓ Authentication successful for {user.email}")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_admin(view_func: Callable) -> Callable:
    """
    Decorator for admin-only endpoints.
    
    Combines token validation + admin role check.
    
    Flow:
    1. First: Execute @require_token logic (token validation + user validation)
    2. Then: Check if user is_staff (admin)
    3. If not admin: return 403 Forbidden
    
    Usage:
        @require_admin
        def admin_only_view(request):
            user = request.user  # Admin user
            ...
    
    Returns:
        Response: View response with optional X-New-Access-Token header
        
    Raises:
        AuthenticationFailed: If token invalid or user not admin
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs) -> Any:
        logger.debug(f"[require_admin] Decorator called for {request.path}")
        
        # Step 1: Extract token
        token = TokenValidator.extract_token(request)
        if not token:
            logger.warning(f"[require_admin] No token provided for {request.path}")
            raise AuthenticationFailed("No token provided")
        
        # Step 2: Try to validate access token
        try:
            validated_token, user = TokenValidator.validate_token(token)
        except AuthenticationFailed:
            # Step 3: Access token invalid, try to refresh
            logger.debug("[require_admin] Access token invalid, attempting refresh...")
            new_token = TokenValidator.refresh_access_token(request)
            
            if not new_token:
                logger.error("[require_admin] Token refresh failed")
                raise AuthenticationFailed("Token expired and refresh failed")
            
            # Validate the new token
            try:
                validated_token, user = TokenValidator.validate_token(new_token)
                setattr(request, 'new_access_token', new_token)
                logger.debug("[require_admin] ✓ New access token will be attached to response")
            except AuthenticationFailed as e:
                logger.error(f"[require_admin] New token validation failed: {str(e)}")
                raise
        
        # Step 4: Validate user (active, exists)
        if not TokenValidator.validate_user(user):
            logger.warning(f"[require_admin] User validation failed")
            raise AuthenticationFailed("User is not valid or inactive")
        
        # Step 5: Check admin permission (is_staff)
        if not user.is_staff:
            logger.warning(f"[require_admin] User {user.email} is not admin (is_staff=False)")
            raise AuthenticationFailed("Admin access required")
        
        # Step 6: Attach user to request and call view
        request.user = user
        logger.debug(f"[require_admin] ✓ Admin authentication successful for {user.email}")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_staff(view_func: Callable) -> Callable:
    """
    Decorator for staff-only endpoints.
    Same as @require_admin - checks if user is_staff.
    
    Usage:
        @require_staff
        def staff_only_view(request):
            user = request.user  # Staff user
            ...
    """
    # Staff decorator is same as admin (checks is_staff flag)
    return require_admin(view_func)


def require_permission(permission: str) -> Callable:
    """
    Decorator for role-based access control (more flexible).
    
    Checks specific permission or user role.
    
    Usage:
        @require_permission('can_edit_items')
        def edit_items_view(request):
            ...
        
        @require_permission('is_superuser')
        def superuser_only_view(request):
            ...
    
    Args:
        permission: Permission name to check (e.g., 'can_edit_items', 'is_superuser', 'is_staff')
    """
    def decorator(view_func: Callable) -> Callable:
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs) -> Any:
            logger.debug(f"[require_permission] Decorator called for {request.path} - checking '{permission}'")
            
            # Step 1-4: Same token validation as require_token
            token = TokenValidator.extract_token(request)
            if not token:
                logger.warning(f"[require_permission] No token provided for {request.path}")
                raise AuthenticationFailed("No token provided")
            
            try:
                validated_token, user = TokenValidator.validate_token(token)
            except AuthenticationFailed:
                logger.debug("[require_permission] Access token invalid, attempting refresh...")
                new_token = TokenValidator.refresh_access_token(request)
                
                if not new_token:
                    logger.error("[require_permission] Token refresh failed")
                    raise AuthenticationFailed("Token expired and refresh failed")
                
                try:
                    validated_token, user = TokenValidator.validate_token(new_token)
                    setattr(request, 'new_access_token', new_token)
                    logger.debug("[require_permission] ✓ New access token will be attached to response")
                except AuthenticationFailed as e:
                    logger.error(f"[require_permission] New token validation failed: {str(e)}")
                    raise
            
            if not TokenValidator.validate_user(user):
                logger.warning(f"[require_permission] User validation failed")
                raise AuthenticationFailed("User is not valid or inactive")
            
            # Step 5: Check specific permission
            has_permission = hasattr(user, permission) and getattr(user, permission)
            
            if not has_permission:
                logger.warning(f"[require_permission] User {user.email} does not have permission '{permission}'")
                raise AuthenticationFailed(f"Permission '{permission}' required")
            
            request.user = user
            logger.debug(f"[require_permission] ✓ User {user.email} has permission '{permission}'")
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


# ── ViewSet method decorators ──────────────────────────────────────────────────
# Use on ViewSet actions instead of function-based views.
# They take (self, request, *args, **kwargs) and *return* a Response on failure
# rather than raising exceptions, so they work cleanly with permission_classes=[].

def _extract_and_validate_user(request):
    """
    Shared token → optional-refresh → validate_user logic.
    Returns (user, None) on success or (None, error_Response) on failure.
    Sets request.new_access_token when a refresh was performed.
    """
    token = TokenValidator.extract_token(request)
    if not token:
        return None, Response({'error': 'No token provided'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        _, user = TokenValidator.validate_token(token)
    except AuthenticationFailed:
        new_token = TokenValidator.refresh_access_token(request)
        if not new_token:
            return None, Response({'error': 'Token expired and refresh failed'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            _, user = TokenValidator.validate_token(new_token)
            setattr(request, 'new_access_token', new_token)
        except AuthenticationFailed as e:
            return None, Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

    if not TokenValidator.validate_user(user):
        return None, Response({'error': 'User is not valid or inactive'}, status=status.HTTP_403_FORBIDDEN)

    request.user = user
    return user, None


# ── Step 1: Authentication ─────────────────────────────────────────────────────

def jwt_authentication(method: Callable) -> Callable:
    """
    Step 1 — Authentication only.
    Validates JWT access token (with auto-refresh via cookie) and sets request.user.
    Must come BEFORE any role-check decorator.

    Usage (standalone — any authenticated user):
        @action(..., permission_classes=[])
        @jwt_authentication
        def my_action(self, request, ...): ...

    Usage (with role gate — stack below jwt_authentication):
        @action(..., permission_classes=[])
        @jwt_authentication
        @role_required(["admin"])
        def admin_only(self, request, ...): ...

    Returns 401 on missing/expired token, 403 on inactive user.
    """
    @functools.wraps(method)
    def wrapper(self, request, *args, **kwargs):
        _, err = _extract_and_validate_user(request)
        if err:
            return err
        return method(self, request, *args, **kwargs)
    return wrapper


# ── Step 2: Role checks (require @jwt_authentication above) ───────────────────

def role_required(roles: list) -> Callable:
    """
    Step 2 — Flexible role check: any role from the list.
    Reads request.user set by @jwt_authentication — does NOT re-validate the token.
    Returns 403 if user does not have any of the required roles.

    Supported roles:
        'admin'    → user.is_admin_role or user.is_staff
        'manager'  → user.is_manager_role or user.has_mgmt_access
        'staff'    → user.is_worker_role or user.is_staff

    Stack order:
        @jwt_authentication         ← runs first (outer)
        @role_required(['admin'])   ← runs second (inner)

    Usage:
        @action(..., permission_classes=[])
        @jwt_authentication
        @role_required(['admin', 'manager'])
        def admin_or_manager_only(self, request, ...): ...

    Returns 401 on unauthenticated, 403 on insufficient role.
    """
    def decorator(method: Callable) -> Callable:
        @functools.wraps(method)
        def wrapper(self, request, *args, **kwargs):
            user = getattr(request, 'user', None)
            if not user or not user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Check if user has any of the required roles
            has_required_role = False
            for role in roles:
                if role == 'admin':
                    if getattr(user, 'is_admin_role', False) or getattr(user, 'is_staff', False):
                        has_required_role = True
                        break
                elif role == 'manager':
                    if getattr(user, 'is_manager_role', False) or getattr(user, 'has_mgmt_access', False):
                        has_required_role = True
                        break
                elif role == 'staff':
                    if getattr(user, 'is_worker_role', False) or getattr(user, 'is_staff', False):
                        has_required_role = True
                        break
            
            if not has_required_role:
                roles_str = ', '.join(roles)
                return Response(
                    {'error': f'One of these roles required: {roles_str}'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            return method(self, request, *args, **kwargs)
        return wrapper
    return decorator


# ── Generic rate limiter ───────────────────────────────────────────────────────

def captcha_guard(
    *,
    fallback_limit: int = 10,
    error_message: str = 'CAPTCHA verification failed. Please complete the challenge.',
):
    """
    Decorator factory — adaptive reCAPTCHA v3 guard.

    Stack BELOW ``@rate_limit`` so this decorator can read ``request._rate_info``
    (set by ``@rate_limit``) to decide whether to require a CAPTCHA token.
    CAPTCHA is triggered when the count reaches 60 % of the rate limit
    (same logic as ``payment_management.decorators.captcha_required``).

    If ``@rate_limit`` is not on the stack the ``fallback_limit`` is used
    to compute the 60 % threshold (CAPTCHA required after
    ``max(1, int(fallback_limit * 0.6))`` requests).

    Args:
        fallback_limit:   Rate limit used when ``request._rate_info`` is absent.
        error_message:    403 response message when CAPTCHA fails.

    Usage::

        @action(detail=False, methods=['post'],
                authentication_classes=[], permission_classes=[])
        @rate_limit(limit=10, window=900, prefix='login', scope='ip')
        @captcha_guard()
        def login(self, request, *args, **kwargs): ...

    The token must be sent by the client as ``recaptcha_token`` in the request
    body once CAPTCHA is triggered.
    """
    from helper.captcha_helpers import verify_captcha, should_require_captcha

    def decorator(method: Callable) -> Callable:
        @functools.wraps(method)
        def wrapper(self, request, *args: Any, **kwargs: Any) -> Any:
            from helper.rate_helpers import _get_ip
            ip = _get_ip(request)

            # Piggyback on @rate_limit counters if already on the stack
            rate = getattr(request, '_rate_info', None)
            count = rate['count'] if rate else 0
            limit = rate['limit'] if rate else fallback_limit

            if should_require_captcha(ip, count, limit):
                from typing import cast as _cast
                token = _cast(dict, request.data).get('recaptcha_token')
                result = verify_captcha(token, remote_ip=ip)
                if not result['success']:
                    logger.warning(
                        f"[captcha_guard] CAPTCHA failed for IP {ip}: "
                        f"{result.get('error')}"
                    )
                    return Response(
                        {'error': error_message},
                        status=status.HTTP_403_FORBIDDEN,
                    )

            return method(self, request, *args, **kwargs)
        return wrapper
    return decorator


def rate_limit(
    limit: int,
    window: int,
    *,
    scope: str = 'ip',
    prefix: str = 'rl',
    error_message: str = 'Too many requests. Please try again later.',
):
    """
    Decorator factory — sliding-window rate limiter for ViewSet methods.

    Args:
        limit:   Maximum number of requests allowed within *window* seconds.
        window:  Window duration in seconds (e.g. 60, 3600).
        scope:   Counter key scope — one of:
                   'ip'      (default) per client IP
                   'user'             per authenticated user
                   'ip+user'          combined (stricter)
        prefix:  Short label for the cache key namespace, e.g. 'login',
                 'change_password'.  Keeps counters separate across endpoints.
        error_message: Custom 429 message.

    Usage — stack BELOW @jwt_authentication (or standalone):

        @action(...)
        @jwt_authentication
        @rate_limit(limit=5, window=3600, prefix='refund')
        def request_refund(self, request, *args, **kwargs): ...

        @action(...)
        @jwt_authentication
        @rate_limit(limit=10, window=60, scope='user', prefix='login')
        def login(self, request, *args, **kwargs): ...

    Side-effects on success:
        request._rate_info = {'allowed', 'count', 'limit', 'window'}
        request._rate_ip   = resolved client IP string

    Returns 429 when the counter exceeds *limit*.
    Falls back gracefully if Redis/cache is unavailable (allows request).
    """
    from helper.rate_helpers import check_rate, build_rate_key

    def decorator(method: Callable) -> Callable:
        @functools.wraps(method)
        def wrapper(self, request, *args: Any, **kwargs: Any) -> Any:
            from django.conf import settings
            if getattr(settings, 'DISABLE_RATE_LIMIT', False):
                return method(self, request, *args, **kwargs)
            from helper.rate_helpers import _get_ip
            ip = _get_ip(request)
            cache_key = build_rate_key(prefix, scope, request)
            rate = check_rate(cache_key, limit, window)

            request._rate_info = rate  # type: ignore[attr-defined]
            request._rate_ip = ip      # type: ignore[attr-defined]

            if not rate['allowed']:
                logger.warning(
                    f"[rate_limit:{prefix}] 429 for key='{cache_key}' "
                    f"count={rate['count']} limit={rate['limit']}"
                )
                return Response(
                    {
                        'error': error_message,
                        'retry_after_seconds': window,
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            return method(self, request, *args, **kwargs)
        return wrapper
    return decorator
