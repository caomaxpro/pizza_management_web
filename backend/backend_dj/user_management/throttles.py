from rest_framework.throttling import SimpleRateThrottle


class UserListUserThrottle(SimpleRateThrottle):
    """
    60 requests/min per authenticated user for the user list endpoint.
    Prevents scraping the full user list repeatedly.
    """
    scope = 'user_list'

    def get_cache_key(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return None  # Fall through to IP throttle
        return self.cache_format % {'scope': self.scope, 'ident': user.pk}


class UserListIpThrottle(SimpleRateThrottle):
    """
    30 requests/min per IP for the user list endpoint.
    Guards against unauthenticated probing even before auth check.
    """
    scope = 'user_list_ip'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


class ChangePasswordUserThrottle(SimpleRateThrottle):
    """
    5 attempts per hour per authenticated user.
    Returns None (no throttle) when the user is anonymous — ChangePasswordIpThrottle covers that case.
    """
    scope = 'change_password_user'

    def get_cache_key(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return None
        return self.cache_format % {'scope': self.scope, 'ident': user.pk}


class ChangePasswordIpThrottle(SimpleRateThrottle):
    """
    20 attempts per hour per IP address (catches unauthenticated probing and distributed attacks).
    """
    scope = 'change_password_ip'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}
