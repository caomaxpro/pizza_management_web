"""
Middleware for JWT Token Management
Attaches refreshed access token to response header if auto-refresh occurred during auth
"""
import logging

logger = logging.getLogger('user_management')


class TokenRefreshMiddleware:
    """
    Middleware that attaches a newly refreshed access token to the response header
    if the authentication process automatically refreshed it
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process request (authentication happens here)
        response = self.get_response(request)
        
        # Check if authentication automatically refreshed the token
        if hasattr(request, 'new_access_token'):
            new_token = request.new_access_token
            logger.debug(f"[Middleware] Attaching new access token to response header for {request.path}")
            # Expose token in header so frontend can update localStorage
            response['X-New-Access-Token'] = new_token
            # Also renew the access_token cookie so the next request doesn't
            # trigger another unnecessary auto-refresh
            response.set_cookie(
                key='access_token',
                value=new_token,
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=5 * 60,  # 5 minutes
                path='/',
            )
        
        return response
