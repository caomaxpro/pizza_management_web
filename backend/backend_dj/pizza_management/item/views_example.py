"""
Example views demonstrating use of @require_token decorator
These are examples - you can apply the decorator to any existing view
"""
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from helper import require_token, require_admin, require_staff, require_permission
from pizza_management.item.model import Item
from pizza_management.item.serializers import ItemSerializer


# Example 1: Simple function-based view with decorator
@require_token
def get_user_items(request):
    """
    Get all items created by authenticated user
    
    Flow:
    1. Decorator validates token
    2. If valid, request.user is set to authenticated user
    3. View executes and returns user's items
    4. If token was refreshed, new token is in response header X-New-Access-Token
    """
    try:
        user = request.user
        items = Item.objects.filter(created_by=user)
        serializer = ItemSerializer(items, many=True)
        
        return Response({
            'success': True,
            'message': f'Retrieved {items.count()} items for user {user.email}',
            'data': serializer.data
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


# Example 2: API view with decorator
@api_view(['GET'])
@require_token
def get_item_by_id(request, item_id):
    """
    Get specific item by ID (requires authentication)
    
    URL: /api/items/{item_id}/detail/
    """
    try:
        user = request.user
        item = Item.objects.get(id=item_id, created_by=user)
        serializer = ItemSerializer(item)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    except Item.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Item not found or access denied'
        }, status=404)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


# Example 3: Multiple decorators (token validation + API view)
@api_view(['POST'])
@require_token
def create_item_authenticated(request):
    """
    Create new item with authenticated user as creator.
    Note: This would normally be in CreateMixin, but shown here for decorator demo.
    
    Request body:
    {
        "name": "Margherita",
        "price": 10.99,
        "description": "Classic pizza"
    }
    """
    try:
        user = request.user
        data = request.data.copy()
        data['created_by'] = user.id  # Set creator to authenticated user
        
        serializer = ItemSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Item created successfully',
                'data': serializer.data
            }, status=201)
        else:
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=400)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


# Example 4: GET with pagination (simple example)
@require_token
def list_items_paginated(request):
    """
    List all items with pagination
    
    Query parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 10)
    """
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        user = request.user
        items = Item.objects.filter(created_by=user)
        
        # Simple pagination calculation
        total_count = items.count()
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        paginated_items = items[start_idx:end_idx]
        serializer = ItemSerializer(paginated_items, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


# Example 5: Showing error scenarios
@require_token
def protected_endpoint(request):
    """
    This endpoint shows possible error responses from decorator:
    
    1. 401 - No token provided
    2. 401 - Token invalid/expired and refresh failed
    3. 403 - User not valid/inactive
    
    If you reach here, token is valid and user is active!
    """
    return Response({
        'success': True,
        'message': 'You have successfully authenticated!',
        'user_email': request.user.email,
        'user_id': request.user.id
    })


# ============================================================================
# ADMIN-ONLY ENDPOINTS
# ============================================================================

@require_admin
def admin_dashboard(request):
    """
    Admin-only view - requires is_staff=True
    
    Flow:
    1. Decorator validates token (same as @require_token)
    2. Check if user.is_staff == True
    3. If not admin → 403 Forbidden
    4. If admin → View executes
    """
    try:
        user = request.user
        return Response({
            'success': True,
            'message': f'Welcome Admin {user.email}',
            'admin_data': {
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'user_id': user.id
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['DELETE'])
@require_admin
def delete_item_admin(request, item_id):
    """
    Admin-only: Delete any item (not just own items)
    
    Requires: token valid + is_staff=True
    """
    try:
        item = Item.objects.get(id=item_id)
        item_name = item.name
        item.delete()
        
        return Response({
            'success': True,
            'message': f'Item "{item_name}" deleted by admin {request.user.email}'
        })
    except Item.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Item not found'
        }, status=404)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@require_staff
def staff_moderation_panel(request):
    """
    Staff-only view (same as @require_admin since both check is_staff)
    
    Requires: token valid + is_staff=True
    """
    try:
        user = request.user
        items_count = Item.objects.count()
        
        return Response({
            'success': True,
            'message': f'Staff moderation panel for {user.email}',
            'stats': {
                'total_items': items_count,
                'staff_member': user.email,
                'is_admin': user.is_staff
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================================================
# FLEXIBLE PERMISSION-BASED ENDPOINTS
# ============================================================================

@require_permission('is_superuser')
def superuser_only_endpoint(request):
    """
    Superuser-only endpoint using @require_permission
    
    Checks: token valid + is_superuser=True
    """
    return Response({
        'success': True,
        'message': f'Superuser endpoint - user: {request.user.email}',
        'is_superuser': request.user.is_superuser
    })


@require_permission('is_staff')
def staff_permission_endpoint(request):
    """
    Staff endpoint using @require_permission
    
    More flexible than @require_staff - you can check any attribute
    """
    return Response({
        'success': True,
        'message': f'Staff permission endpoint - user: {request.user.email}',
        'is_staff': request.user.is_staff
    })
