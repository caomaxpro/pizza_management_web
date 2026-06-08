"""
Custom JWT Authentication for Cookie-based Auth
Reads JWT tokens from cookies instead of (or in addition to) Authorization header
Automatically refreshes expired access tokens using refresh token
"""
import logging
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed as JWTAuthenticationFailed, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger('user_management')


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads tokens from httpOnly cookies
    Falls back to Authorization header if cookie not present
    Automatically refreshes expired access tokens if refresh token is valid
    """
    
    def authenticate(self, request):
        """
        Authenticate using JWT from cookies, falling back to Authorization header
        Automatically refresh expired access token if refresh token is available
        """
        logger.debug(f"[Auth] authenticate() called for {request.path}")
        logger.debug(f"[Auth] All cookies: {request.COOKIES}")
        
        # Try to get token from cookies first
        raw_token = request.COOKIES.get('access_token')
        logger.debug(f"[Auth] access_token from cookies: {raw_token[:20] if raw_token else '(not found)'}...")
        
        # If no token in cookies, try Authorization header
        if not raw_token:
            # Try Authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            logger.debug(f"[Auth] Authorization header: {auth_header[:20] if auth_header else '(not found)'}...")
            
            if auth_header.startswith('Bearer '):
                raw_token = auth_header[7:]  # Remove 'Bearer ' prefix
                logger.debug(f"[Auth] Found token in Authorization header")
            else:
                logger.debug(f"[Auth] No token found in cookies or Authorization header")
                return None  # No token found, let other auth methods handle it
        
        try:
            # Use parent class method to validate token with correct token type
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            logger.debug(f"[Auth] ✓ User authenticated: {user.email}")
            
            return (user, validated_token)
        except (InvalidToken, TokenError) as ex:
            # Access token is invalid/expired, try to refresh it
            logger.debug(f"[Auth] Access token invalid: {str(ex)}")
            logger.debug(f"[Auth] Attempting automatic token refresh...")
            
            # Try to get refresh token from cookies only (httpOnly)
            # Do NOT try Authorization header - it only contains access_token
            refresh_token_raw = request.COOKIES.get('refresh_token')
            if refresh_token_raw:
                logger.debug(f"[Auth] Found refresh_token in cookies")
                try:
                    # Validate and refresh the refresh token
                    refresh_token = RefreshToken(refresh_token_raw)
                    new_access_token_str = str(refresh_token.access_token)
                    
                    # Validate the new access token (get_validated_token expects bytes)
                    validated_token = self.get_validated_token(new_access_token_str.encode())
                    user = self.get_user(validated_token)
                    
                    # Store new token on request for middleware to attach to response
                    setattr(request, 'new_access_token', new_access_token_str)
                    logger.debug(f"[Auth] ✓ Access token refreshed automatically for {user.email}")
                    
                    return (user, validated_token)
                except (InvalidToken, TokenError) as refresh_ex:
                    logger.error(f"[Auth] Refresh token also invalid: {str(refresh_ex)}")
                    raise AuthenticationFailed("Token refresh failed")
            else:
                logger.debug(f"[Auth] No refresh token found in cookies - cannot refresh access token")
                raise AuthenticationFailed("Authentication failed")
        except JWTAuthenticationFailed as ex:
            logger.error(f"[Auth] JWTAuthenticationFailed: {str(ex)}")
            raise AuthenticationFailed(str(ex))
