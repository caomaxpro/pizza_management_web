"""
Celery Tasks for Pizza Management
Background tasks for archival and maintenance operations
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.serializers import serialize
import logging
import json
import os
from pathlib import Path

from order_management.order.model import Order
from order_management.order.orderitem_model import OrderItem

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def archive_old_orders(self, days=180):
    """
    Archive old orders to JSON file and delete from database.
    Runs every 6 months to maintain optimal DB performance.
    
    Args:
        days (int): Number of days to keep in DB (default 180 = 6 months)
        
    Returns:
        dict: Status, number of archived orders, and backup file path
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Query orders created before cutoff_date
        old_orders = Order.objects.filter(created_at__lt=cutoff_date).prefetch_related('items', 'user')
        order_count = old_orders.count()
        
        if order_count == 0:
            logger.info(f"No orders to archive (cutoff: {cutoff_date})")
            return {
                'status': 'success',
                'archived': 0,
                'message': 'No orders to archive'
            }
        
        # Prepare archive directory
        archive_dir = Path(settings.BASE_DIR) / 'assets' / 'archives' / 'orders'
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Create backup filename with timestamp
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_file = archive_dir / f"orders_archive_{timestamp}.json"
        
        # Serialize orders with related data
        archive_data = {
            'archive_date': timezone.now().isoformat(),
            'cutoff_date': cutoff_date.isoformat(),
            'order_count': order_count,
            'orders': []
        }
        
        for order in old_orders:
            order_dict = {
                'id': order.id,
                'user_id': order.user.id if order.user else None,
                'user_email': order.user.email if order.user else None,
                'status': order.status,
                'total_price': str(order.total_price),
                'cancellation_fee': str(order.cancellation_fee) if order.cancellation_fee else None,
                'cancellation_reason': order.cancellation_reason,
                'notes': order.notes,
                'order_date': order.order_date.isoformat(),
                'delivery_date': order.delivery_date.isoformat() if order.delivery_date else None,
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat(),
                'items': []
            }
            
            # Add related order items
            for oi in order.items.all():
                item_dict = {
                    'id': oi.id,
                    'item_id': oi.item.id if oi.item else None,
                    'item_name': oi.customizations.get('item_name', '') if oi.customizations else '',
                    'quantity': oi.quantity,
                    'unit_price': str(oi.unit_price),
                    'subtotal': str(oi.subtotal),
                    'notes': oi.notes,
                    'customizations': oi.customizations,
                }
                order_dict['items'].append(item_dict)
            
            archive_data['orders'].append(order_dict)
        
        # Write to JSON file
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(archive_data, f, indent=2, ensure_ascii=False)
        
        # Delete archived orders from database
        deleted_count, breakdown = old_orders.delete()
        
        message = f"Archived {order_count} orders to {backup_file.name} and deleted from DB"
        logger.info(message)
        logger.info(f"Deletion breakdown: {breakdown}")
        
        return {
            'status': 'success',
            'archived': order_count,
            'backup_file': str(backup_file),
            'message': message,
            'breakdown': breakdown
        }
        
    except Exception as exc:
        logger.error(f"Archive task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def verify_archive_integrity(archive_file_path):
    """
    Verify that archived backup file is valid and readable.
    
    Args:
        archive_file_path (str): Path to the archive JSON file
        
    Returns:
        dict: Verification status and file info
    """
    try:
        if not os.path.exists(archive_file_path):
            return {
                'status': 'error',
                'message': f"Archive file not found: {archive_file_path}"
            }
        
        # Verify JSON is readable
        with open(archive_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        file_size = os.path.getsize(archive_file_path)
        order_count = data.get('order_count', 0)
        
        logger.info(f"Archive verified: {order_count} orders, {file_size} bytes")
        
        return {
            'status': 'success',
            'archive_file': archive_file_path,
            'order_count': order_count,
            'file_size_bytes': file_size,
            'message': 'Archive integrity verified'
        }
        
    except json.JSONDecodeError as exc:
        logger.error(f"Archive JSON corrupt: {str(exc)}")
        return {
            'status': 'error',
            'message': f"JSON decode error: {str(exc)}"
        }
    except Exception as exc:
        logger.error(f"Archive verification failed: {str(exc)}")
        return {
            'status': 'error',
            'message': str(exc)
        }
