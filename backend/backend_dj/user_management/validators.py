"""
User Management Validators
Custom validators for user data
"""
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model

User = get_user_model()


class UserValidators:
    """Custom validators for user operations"""
    
    @staticmethod
    def validate_email_unique(email: str):
        """Validate that email is unique"""
        if User.objects.filter(email=email).exists():
            raise ValueError("Email already registered")
        return email
    
    @staticmethod
    def validate_username_unique(username: str):
        """Validate that username is unique"""
        if User.objects.filter(username=username).exists():
            raise ValueError("Username already taken")
        return username
    
    @staticmethod
    def validate_password_strength(password: str):
        """Validate password strength"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        return password


class AddressValidators:
    """Custom validators for address operations"""
    
    @staticmethod
    def validate_postal_code(postal_code: str):
        """Validate postal code format"""
        if not postal_code.strip():
            raise ValueError("Postal code cannot be empty")
        return postal_code
