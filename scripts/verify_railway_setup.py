#!/usr/bin/env python
"""
Railway Setup Verification Script
Verify that Railway configuration protects database data.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.conf import settings
from django.db import connection

def check_database_backend():
    """Check that we're using PostgreSQL, not SQLite."""
    db_backend = settings.DATABASES['default']['ENGINE']
    print(f"✓ Database Backend: {db_backend}")
    
    if db_backend == 'django.db.backends.sqlite3':
        print("❌ ERROR: Using SQLite in production!")
        print("This will cause data loss on redeploy.")
        return False
    
    if db_backend == 'django.db.backends.postgresql':
        print("✓ PostgreSQL detected - Good!")
        return True
    
    print(f"⚠️  WARNING: Unknown database backend: {db_backend}")
    return False

def check_database_url():
    """Check DATABASE_URL environment variable."""
    db_url = os.getenv('DATABASE_URL', '')
    print(f"✓ DATABASE_URL length: {len(db_url)} characters")
    
    if not db_url:
        print("❌ ERROR: DATABASE_URL not set!")
        return False
    
    if 'sqlite' in db_url.lower():
        print("❌ ERROR: DATABASE_URL points to SQLite!")
        return False
    
    if 'postgres' in db_url.lower():
        print("✓ DATABASE_URL points to PostgreSQL - Good!")
        return True
    
    print(f"⚠️  WARNING: DATABASE_URL format unknown")
    return False

def check_allow_sqlite_fallback():
    """Check ALLOW_SQLITE_FALLBACK setting."""
    allow_fallback = os.getenv('ALLOW_SQLITE_FALLBACK', 'False').lower()
    print(f"✓ ALLOW_SQLITE_FALLBACK: {allow_fallback}")
    
    if allow_fallback == 'true':
        print("❌ ERROR: ALLOW_SQLITE_FALLBACK is True!")
        print("This may cause data loss if PostgreSQL fails.")
        return False
    
    if allow_fallback == 'false':
        print("✓ ALLOW_SQLITE_FALLBACK is False - Good!")
        return True
    
    print(f"⚠️  WARNING: ALLOW_SQLITE_FALLBACK value unknown: {allow_fallback}")
    return False

def check_debug_mode():
    """Check DEBUG setting."""
    debug = settings.DEBUG
    print(f"✓ DEBUG: {debug}")
    
    if debug:
        print("⚠️  WARNING: DEBUG is True in production!")
        print("This may expose sensitive information.")
        return False
    
    print("✓ DEBUG is False - Good!")
    return True

def check_database_connection():
    """Test database connection."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result[0] == 1:
                print("✓ Database connection successful - Good!")
                return True
    except Exception as e:
        print(f"❌ ERROR: Database connection failed: {e}")
        return False

def count_data():
    """Count records in main tables."""
    try:
        from django.contrib.auth.models import User
        from properties.models import Property, Broker
        
        user_count = User.objects.count()
        property_count = Property.objects.count()
        broker_count = Broker.objects.count()
        
        print(f"✓ Users: {user_count}")
        print(f"✓ Properties: {property_count}")
        print(f"✓ Brokers: {broker_count}")
        
        return True
    except Exception as e:
        print(f"⚠️  WARNING: Could not count data: {e}")
        return False

def check_file_ignores():
    """Check that database files are in .gitignore."""
    gitignore_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.gitignore')
    
    if not os.path.exists(gitignore_path):
        print("⚠️  WARNING: .gitignore not found")
        return False
    
    with open(gitignore_path, 'r') as f:
        gitignore_content = f.read()
    
    required_ignores = ['db.sqlite3', '*.sqlite3', 'muq.sqlite3']
    all_found = True
    
    for ignore in required_ignores:
        if ignore in gitignore_content:
            print(f"✓ {ignore} is in .gitignore")
        else:
            print(f"❌ ERROR: {ignore} is NOT in .gitignore!")
            all_found = False
    
    return all_found

def main():
    """Run all checks."""
    print("=" * 60)
    print("Railway Setup Verification")
    print("=" * 60)
    print()
    
    checks = [
        ("Database Backend", check_database_backend),
        ("DATABASE_URL", check_database_url),
        ("ALLOW_SQLITE_FALLBACK", check_allow_sqlite_fallback),
        ("DEBUG Mode", check_debug_mode),
        ("Database Connection", check_database_connection),
        ("Data Count", count_data),
        (".gitignore", check_file_ignores),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n--- {name} ---")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Total: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✓ All checks passed! Railway setup is correct.")
        print("Your data should be safe on redeploy.")
        return 0
    else:
        print("\n❌ Some checks failed! Please fix the issues above.")
        print("Your data may be at risk on redeploy.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
