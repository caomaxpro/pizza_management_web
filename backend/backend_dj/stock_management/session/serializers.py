from rest_framework import serializers
from stock_management.session.model import StockTakeSession


class StockTakeSessionSerializer(serializers.ModelSerializer):
    started_by_username = serializers.CharField(source='started_by.username', read_only=True, default=None)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True, default=None)
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = StockTakeSession
        fields = [
            'id',
            'started_by',
            'started_by_username',
            'assigned_to',
            'assigned_to_username',
            'task_type',
            'task_type_display',
            'status',
            'status_display',
            'notes',
            'started_at',
            'expires_at',
            'closed_at',
        ]
        read_only_fields = [
            'id',
            'started_by',
            'started_by_username',
            'assigned_to_username',
            'task_type_display',
            'status_display',
            'started_at',
            'closed_at',
        ]
