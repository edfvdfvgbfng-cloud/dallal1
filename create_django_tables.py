#!/usr/bin/env python
"""
Manually create Django core tables to ensure they exist.
This is a fallback when migrate command fails.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from django.db import connection
from django.core.management import call_command

def create_django_tables():
    """Create Django core tables manually"""
    print("Creating Django core tables manually...")
    
    cursor = connection.cursor()
    
    # List of Django core tables that must exist
    django_tables = [
        'django_migrations',
        'django_content_type',
        'auth_permission',
        'auth_user',
        'auth_group',
        'auth_group_permissions',
        'auth_user_groups',
        'auth_user_user_permissions',
        'django_session',
        'django_admin_log',
    ]
    
    # Check which tables exist
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Existing tables: {len(existing_tables)}")
    for table in django_tables:
        if table in existing_tables:
            print(f"  ✓ {table} exists")
        else:
            print(f"  ✗ {table} MISSING")
    
    # Try to run syncdb to create missing tables
    print("\nAttempting to run syncdb to create missing tables...")
    try:
        call_command('syncdb', interactive=False, verbosity=2)
        print("✓ syncdb completed successfully")
    except Exception as e:
        print(f"✗ syncdb failed: {e}")
    
    # Verify tables were created
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    new_existing_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\nAfter syncdb: {len(new_existing_tables)} tables exist")
    for table in django_tables:
        if table in new_existing_tables:
            print(f"  ✓ {table} exists")
        else:
            print(f"  ✗ {table} STILL MISSING")
    
    # Return success if all core tables exist
    missing = [t for t in django_tables if t not in new_existing_tables]
    if missing:
        print(f"\n❌ ERROR: Missing core tables: {missing}")
        return False
    else:
        print(f"\n✅ SUCCESS: All Django core tables exist")
        return True

if __name__ == '__main__':
    success = create_django_tables()
    exit(0 if success else 1)
