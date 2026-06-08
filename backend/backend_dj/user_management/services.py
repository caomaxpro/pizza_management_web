"""
User Management Services
Business logic for user operations
"""
from .models import User, Address
import logging
logger = logging.getLogger(__name__)


class UserService:
    """Service for user operations"""
    
    @staticmethod
    def create_user(email: str, username: str, password: str, **kwargs):
        """
        Create a new user
        
        Args:
            email: User email
            username: Username
            password: User password
            **kwargs: Additional fields
            
        Returns:
            User instance
        """
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            **kwargs
        )
        logger.info(f"User created: {user.email}")
        return user
    
    @staticmethod
    def update_user(user: User, **kwargs):
        """
        Update user information
        
        Args:
            user: User instance
            **kwargs: Fields to update
            
        Returns:
            Updated User instance
        """
        for field, value in kwargs.items():
            if hasattr(user, field):
                setattr(user, field, value)
        user.save()
        logger.info(f"User updated: {user.email}")
        return user
    
    @staticmethod
    def change_password(user: User, old_password: str, new_password: str):
        """
        Change user password
        
        Args:
            user: User instance
            old_password: Current password
            new_password: New password
            
        Returns:
            Updated User instance
        """
        if not user.check_password(old_password):
            raise ValueError("Invalid old password")
        
        user.set_password(new_password)
        user.save()
        logger.info(f"Password changed for: {user.email}")
        return user
    
    @staticmethod
    def create_address(user: User, **kwargs):
        """
        Create address for user
        
        Args:
            user: User instance
            **kwargs: Address fields
            
        Returns:
            Address instance
        """
        address = Address.objects.create(user=user, **kwargs)
        logger.info(f"Address created for user: {user.email}")
        return address
    
    @staticmethod
    def set_default_address(address: Address):
        """
        Set address as default
        
        Args:
            address: Address instance
            
        Returns:
            Address instance
        """
        # Clear other defaults
        Address.objects.filter(user=address.user).update(is_default=False)
        address.is_default = True
        address.save()
        logger.info(f"Default address set: {address.id}")
        return address
