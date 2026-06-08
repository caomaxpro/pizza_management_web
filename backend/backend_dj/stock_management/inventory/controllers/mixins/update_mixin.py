# inventory/controllers/mixins/update_mixin.py
import json
import logging
from datetime import timedelta
from typing import Any, cast
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from pydantic import ValidationError as PydanticValidationError

from stock_management.models import Inventory, InventoryLog
from stock_management.inventory.validators import validate_inventory_data, BulkLogCreateValidator
from stock_management.inventory.serializers import InventorySerializer, InventoryLogSerializer
from stock_management.inventory.services import InventoryService
from stock_management.permissions import can_approve_override
from user_management.models import User
from helper.auth_decorators import jwt_authentication, role_required
from rest_framework.request import Request

logger = logging.getLogger(__name__)


class UpdateMixin:
    """
    Mixin to handle PUT/PATCH requests for updating inventory items.
    Pattern: Like pizza_management.ingredient - no class attributes
    """
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    def update(self, request, *args, **kwargs) -> Response:
        """
        Full update (PUT) of inventory item (Admin/Manager only).
        PUT /api/inventory/{id}/
        """
        partial = kwargs.pop('partial', False)
        pk = kwargs.get('pk')
        if not pk:
            return Response({'error': 'ID not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            instance = Inventory.objects.get(pk=pk)
        except Inventory.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            if not partial:
                validate_inventory_data(request.data)
            else:
                self._validate_partial_update(dict(request.data), instance)
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = InventorySerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)
    
    def partial_update(self, request: "Request", *args: Any, **kwargs: Any) -> Response:
        """
        Partial update (PATCH) of inventory item.
        PATCH /api/inventory/{id}/
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def _validate_partial_update(self, data: dict, instance: Inventory) -> None:
        """Validate partial update by merging with existing data"""
        merged_data = {
            'name': data.get('name', instance.name),
            'description': data.get('description', instance.description),
            'unit': data.get('unit', instance.unit),
            'current_stock': float(data.get('current_stock', instance.current_stock)),
            'min_threshold': float(data.get('min_threshold', instance.min_threshold)),
            'max_threshold': float(data.get('max_threshold', instance.max_threshold)) if data.get('max_threshold') or instance.max_threshold else None,
            'is_active': data.get('is_active', instance.is_active),
        }
        # Pass exclude_id to exclude the current instance from duplicate name check
        validate_inventory_data(merged_data, exclude_id=instance.pk)
    
    def perform_update(self, serializer: Any) -> None:
        """Save updated inventory item"""
        serializer.save()

    @action(detail=False, methods=['post'], url_path='revert-logs', permission_classes=[])
    @jwt_authentication
    @role_required(["admin", "manager"])
    def revert_logs(self, request) -> Response:
        """
        Revert a set of InventoryLog entries by creating compensating entries.

        Accepts: { "log_ids": [1, 2, 3], "force": false }

        Rollback eligibility (non-admins):
          A log is revertible if EITHER:
            (a) it was created within the last 24 hours, OR
            (b) it is one of the last 5 logs for its inventory item.
          Admins (role='admin' or is_superuser) may pass "force": true to bypass
          these limits.

        Returns 400 with ineligible_logs details if any log fails the check (
        unless the user is an admin with force=true).
        Returns 201 with the newly created reverse log entries on success.
        """
        user = cast(User, request.user)
        log_ids = request.data.get('log_ids', [])
        if not log_ids or not isinstance(log_ids, list):
            return Response(
                {'error': 'log_ids must be a non-empty list'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logs = list(
            InventoryLog.objects.select_related('inventory').filter(id__in=log_ids)
        )
        found_ids = {log.id for log in logs}
        missing = set(log_ids) - found_ids
        if missing:
            return Response(
                {'error': f'Log IDs not found: {sorted(missing)}'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ------------------------------------------------------------------ #
        # Rollback eligibility check                                          #
        # ------------------------------------------------------------------ #
        is_admin = can_approve_override(user) or user.is_superuser
        force = bool(request.data.get('force', False))

        if not (is_admin and force):
            cutoff = timezone.now() - timedelta(hours=24)

            # Collect last-5 log IDs for each inventory referenced in this batch
            inventory_ids = {log.inventory.id for log in logs}
            last5_ids: set[int] = set()
            for inv_id in inventory_ids:
                ids = list(
                    InventoryLog.objects.filter(inventory_id=inv_id)
                    .order_by('-created_at')
                    .values_list('id', flat=True)[:5]
                )
                last5_ids.update(ids)

            ineligible = []
            for log in logs:
                is_recent = log.created_at >= cutoff
                in_last5 = log.id in last5_ids
                if not (is_recent or in_last5):
                    ineligible.append({
                        'id': log.id,
                        'created_at': log.created_at.isoformat(),
                        'reason': (
                            'Log is older than 24 hours and not among the last '
                            '5 entries for this inventory item. An admin can '
                            'bypass this limit by passing "force": true.'
                        ),
                    })

            if ineligible:
                return Response(
                    {
                        'error': 'Some logs cannot be reverted (outside rollback window)',
                        'ineligible_logs': ineligible,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ------------------------------------------------------------------ #
        # Build compensating entries and apply                                #
        # ------------------------------------------------------------------ #
        entries = [
            {
                'inventory_id': log.inventory.id,
                'quantity_change': -log.quantity_change,
                'reason_type': 'stock_take',
                'reason_detail': f'Revert of log #{log.id}',
            }
            for log in logs
        ]

        try:
            reverse_logs = InventoryService.create_logs_and_apply(entries)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = InventoryLogSerializer(reverse_logs, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='bulk-create', permission_classes=[])
    @jwt_authentication
    def bulk_create(self, request) -> Response:
        """
        Atomically create multiple InventoryLog entries and update stock.
        POST /api/inventory-log/bulk-create/

        Expected payload:
            { "entries": [ {inventory_id, quantity_change, reason_type, reason_detail?}, ... ] }

        Permission rules:
          - admin / manager : always allowed
          - staff           : allowed only if they have the matching task permission
                              (can_stock_take for 'stock_take', can_receive_stock for 'receipt')
        """
        user = cast(User, request.user)
        if not user or not user.is_authenticated:
            logger.warning(f"Unauthenticated bulk_create attempt from {request.META.get('REMOTE_ADDR')}")
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        entries_count = len(request.data.get('entries', []))
        logger.info(f"bulk_create started: user={user.id} (role={getattr(user, 'role', 'unknown')}), entries={entries_count}")

        role = getattr(user, 'role', None)
        is_privileged = role in ('admin', 'manager') or getattr(user, 'is_superuser', False)

        if not is_privileged:
            if role != 'staff':
                logger.warning(f"Permission denied for bulk_create: user={user.id}, role={role} (not staff/admin/manager)")
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

            # Staff: validate per-entry reason_type against task permissions
            entries_raw = request.data.get('entries', [])
            logger.debug(f"Staff permission check: user={user.id}, can_stock_take={getattr(user, 'can_stock_take', False)}, can_receive_stock={getattr(user, 'can_receive_stock', False)}")
            for entry in entries_raw:
                reason = entry.get('reason_type')
                if reason == 'stock_take' and not getattr(user, 'can_stock_take', False):
                    logger.warning(f"Staff user {user.id} denied stock_take permission")
                    return Response(
                        {'error': 'You do not have permission to perform stock takes.'},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                if reason == 'receipt' and not getattr(user, 'can_receive_stock', False):
                    logger.warning(f"Staff user {user.id} denied receipt permission")
                    return Response(
                        {'error': 'You do not have permission to receive stock.'},
                        status=status.HTTP_403_FORBIDDEN,
                    )

        try:
            validated = BulkLogCreateValidator(entries=request.data.get('entries', []))
            logger.debug(f"Validation passed: {entries_count} entries for user={user.id}")
        except PydanticValidationError as e:
            logger.error(f"Validation error in bulk_create for user={user.id}: {e.json()}")
            return Response({'errors': json.loads(e.json())}, status=status.HTTP_400_BAD_REQUEST)

        try:
            logs = InventoryService.create_logs_and_apply([
                entry.model_dump() for entry in validated.entries
            ])
            logger.info(f"bulk_create success: user={user.id}, created {len(logs)} logs")
        except ValueError as e:
            logger.error(f"Service error in bulk_create for user={user.id}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = InventoryLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
