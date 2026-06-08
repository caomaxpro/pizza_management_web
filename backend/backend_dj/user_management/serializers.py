"""
User Management Serializers
Serializers for User and Address models
"""
import datetime
from rest_framework import serializers
from .models import User, Address, Task, RoleTask, WorkSchedule, ShiftTaskPermission


class UserSerializer(serializers.ModelSerializer):
    """Serializer for customer self-registration and general user views."""
    password = serializers.CharField(write_only=True, min_length=8, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'role', 'is_active', 'is_staff', 'date_joined', 'created_at',
            'password',
        ]
        read_only_fields = ['id', 'date_joined', 'created_at']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class StaffUserSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating staff accounts (admin/manager only).
    Exposes role and password (write-only).
    Role and per-staff task flags are read-only for non-admin/manager callers.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    role_tasks = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'role', 'can_stock_take', 'can_receive_stock',
            'is_active', 'password',
            'date_joined', 'created_at', 'role_tasks',
        ]
        read_only_fields = ['id', 'date_joined', 'created_at']

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request is None:
            return fields
        caller = getattr(request, 'user', None)
        # Only admin/manager may write role and per-staff task flags
        if caller is None or not caller.has_mgmt_access:
            for field_name in ('role', 'can_stock_take', 'can_receive_stock'):
                if field_name in fields:
                    fields[field_name].read_only = True
        return fields

    def get_role_tasks(self, obj: User):
        """Return the task codenames allowed for this user's role."""
        qs = RoleTask.objects.filter(role=obj.role, allowed=True).select_related('task')
        return [rt.task.codename for rt in qs]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for User with addresses"""
    addresses = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'is_active', 'is_staff', 'google_id', 'facebook_id',
            'date_joined', 'created_at', 'addresses'
        ]
        read_only_fields = ['id', 'date_joined', 'created_at', 'google_id', 'facebook_id']
    
    def get_addresses(self, obj):
        """Get user's addresses"""
        addresses = obj.addresses.all()
        return AddressSerializer(addresses, many=True).data


class AddressSerializer(serializers.ModelSerializer):
    """Serializer for Address model"""
    
    class Meta:
        model = Address
        fields = [
            'id', 'street', 'city', 'state', 'postal_code', 'country',
            'latitude', 'longitude', 'is_default', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ShiftTaskPermissionSerializer(serializers.ModelSerializer):
    """Serializer for per-shift task permission entries."""

    class Meta:
        model = ShiftTaskPermission
        fields = ['id', 'day', 'shift_start', 'can_stock_take', 'can_receive_stock']
        read_only_fields = ['id']


class WorkScheduleSerializer(serializers.ModelSerializer):
    """Serializer for WorkSchedule model."""
    assigned_to_username = serializers.CharField(
        source='assigned_to.username', read_only=True
    )
    assigned_to_role = serializers.CharField(
        source='assigned_to.role', read_only=True
    )
    assigned_to_email = serializers.CharField(
        source='assigned_to.email', read_only=True, default=None
    )
    created_by_username = serializers.CharField(
        source='created_by.username', read_only=True, default=None
    )
    shift_task_perms = ShiftTaskPermissionSerializer(many=True, read_only=True)

    class Meta:
        model = WorkSchedule
        fields = [
            'id',
            'created_by', 'created_by_username',
            'assigned_to', 'assigned_to_username', 'assigned_to_role', 'assigned_to_email',
            'week_start', 'entries', 'notes', 'active',
            'created_at', 'updated_at',
            'shift_task_perms',
        ]
        read_only_fields = [
            'id', 'created_by', 'created_at', 'updated_at',
            'created_by_username', 'assigned_to_username', 'assigned_to_role', 'assigned_to_email',
            'shift_task_perms',
        ]

    def validate_week_start(self, value: datetime.date) -> datetime.date:
        """Ensure week_start is a Monday."""
        if value.weekday() != 0:  # 0 = Monday
            raise serializers.ValidationError(
                'week_start must be a Monday (ISO week start).'
            )
        return value

    def validate_entries(self, value: dict) -> dict:
        allowed_keys = {'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'}
        invalid_keys = set(value.keys()) - allowed_keys
        if invalid_keys:
            raise serializers.ValidationError(
                f'Invalid day keys: {invalid_keys}. Allowed: mon tue wed thu fri sat sun'
            )
        return value
