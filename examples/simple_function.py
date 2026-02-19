#!/usr/bin/env python3
"""
Simple user management module.
"""

def create_user(username, email, password):
    """Create a new user account."""
    user = {
        'username': username,
        'email': email,
        'password': password
    }
    return user

def validate_email(email):
    """Validate email format."""
    return '@' in email

def get_user_by_id(user_id):
    """Retrieve user by ID."""
    # TODO: Implement database lookup
    return None

def update_user(user_id, data):
    """Update user information."""
    # TODO: Implement update logic
    pass

def delete_user(user_id):
    """Delete a user account."""
    # TODO: Implement deletion
    pass
