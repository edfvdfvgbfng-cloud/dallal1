#!/usr/bin/env python
"""
Script to create admin user for Railway deployment
Run this after migrations to create the initial admin user
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_admin_user():
    """Create admin user if it doesn't exist"""
    username = 'muq'
    password = '12345'
    email = 'muq@example.com'
    
    try:
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            print(f"User '{username}' already exists. Skipping creation.")
            user = User.objects.get(username=username)
            print(f"User details: {user.username} ({user.email})")
            return
        
        # Create superuser
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        
        print(f"✅ Admin user created successfully!")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   Email: {email}")
        print(f"   Superuser: Yes")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        raise

if __name__ == '__main__':
    create_admin_user()