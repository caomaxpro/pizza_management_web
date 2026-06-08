"""Delete Mixin for Payment operations"""
from typing import Any
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from helper.auth_decorators import jwt_authentication, role_required


class DeleteMixin:
    """Mixin for delete operations"""
    
    def get_object(self) -> Any:
        """Get object instance - should be implemented in ViewSet"""
        raise NotImplementedError("Subclass must implement get_object()")
    
    def perform_destroy(self, instance: Any) -> None:
        """Handle delete operation"""
        instance.delete()
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delete a record"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
