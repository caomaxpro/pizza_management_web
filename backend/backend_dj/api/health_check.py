# backend/backend_dj/api/views.py - Add to this file or create if doesn't exist

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache
from django.db import connections
from django.db.utils import OperationalError
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
def health_check(request):
    """Health check endpoint for monitoring and deployment verification"""
    health_status = {
        "status": "ok",
        "services": {}
    }
    
    all_ok = True
    
    # Check Database
    try:
        connections['default'].ensure_connection()
        health_status["services"]["database"] = "healthy"
    except OperationalError as e:
        logger.error(f"Database health check failed: {e}")
        health_status["services"]["database"] = "unhealthy"
        all_ok = False
    
    # Check Redis Cache
    try:
        cache.set('health_check_test', 'ok', 10)
        test_value = cache.get('health_check_test')
        if test_value == 'ok':
            health_status["services"]["cache"] = "healthy"
        else:
            health_status["services"]["cache"] = "unhealthy"
            all_ok = False
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        health_status["services"]["cache"] = "unhealthy"
        all_ok = False
    
    if not all_ok:
        health_status["status"] = "degraded"
    
    status_code = 200 if all_ok else 503
    return Response(health_status, status=status_code)
