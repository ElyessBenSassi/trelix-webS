"""
Custom authentication backend for SPARQL Person authentication.
Provides user.is_authenticated support for SPARQL-based authentication.
"""
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import AnonymousUser


class SPARQLPerson:
    """Simple user-like object for SPARQL Person authentication"""
    def __init__(self, person_uri, name, email, role_uri=None, role_label=None):
        self.uri = person_uri
        self.username = email
        self.name = name
        self.email = email
        self.role_uri = role_uri
        self.role_label = role_label
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
    
    def __str__(self):
        return self.name or self.email
    
    def get_full_name(self):
        return self.name
    
    def get_short_name(self):
        return self.name.split()[0] if self.name else self.email.split('@')[0]
    
    def is_administrator(self):
        """Check if user has Administrator role"""
        if not self.role_uri and not self.role_label:
            return False
        # Check if role contains Administrator
        role_str = (self.role_label or self.role_uri or "").lower()
        return "administrator" in role_str
    
    def is_instructor(self):
        """Check if user has Instructor role"""
        if not self.role_uri and not self.role_label:
            return False
        # Check if role contains Instructor
        role_str = (self.role_label or self.role_uri or "").lower()
        return "instructor" in role_str
    
    def can_create_activity(self):
        """Check if user can create activities (Administrator or Instructor)"""
        return self.is_administrator() or self.is_instructor()
    
    @property
    def is_admin(self):
        """Property for template access"""
        return self.is_administrator()
    
    @property
    def can_create(self):
        """Property for template access to activity creation"""
        return self.can_create_activity()


class SPARQLPersonAuthBackend(BaseBackend):
    """Authentication backend that checks session for SPARQL Person"""
    
    def authenticate(self, request, **kwargs):
        # We don't use this for authentication, it's handled by views
        return None
    
    def get_user(self, user_id):
        # We don't use Django User model
        return None

