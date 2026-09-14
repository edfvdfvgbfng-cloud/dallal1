"""
Migration to classify existing users into proper user types
This migration:
1. Adds user_type field to UserProfile (already done in model)
2. Classifies existing users based on their current state
3. Ensures data integrity and proper type classification
"""

from django.db import migrations
from django.db.models import Q


def classify_user_types(apps, schema_editor):
    """Classify existing users into proper user types."""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Step 1: Add user_type column if it doesn't exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'properties_userprofile' 
            AND column_name = 'user_type';
        """)
        
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE properties_userprofile 
                ADD COLUMN user_type VARCHAR(10) 
                DEFAULT 'user' 
                NOT NULL 
                CHECK (user_type IN ('user', 'broker', 'admin'));
            """)
            print("Added user_type column to UserProfile")
        
        # Step 2: Classify existing users
        # Mark superusers as admin
        cursor.execute("""
            UPDATE properties_userprofile up
            SET user_type = 'admin'
            FROM auth_user u
            WHERE up.user_id = u.id AND u.is_superuser = TRUE;
        """)
        print("Classified superusers as admin")
        
        # Mark users with broker profiles as broker
        cursor.execute("""
            UPDATE properties_userprofile up
            SET user_type = 'broker'
            FROM properties_broker b
            WHERE up.user_id = b.user_id;
        """)
        print("Classified users with broker profiles as broker")
        
        # Step 3: Verify classification
        cursor.execute("""
            SELECT user_type, COUNT(*) as count
            FROM properties_userprofile
            GROUP BY user_type;
        """)
        
        results = cursor.fetchall()
        print("User type classification:")
        for user_type, count in results:
            print(f"  {user_type}: {count}")


def reverse_classify_user_types(apps, schema_editor):
    """Reverse the classification (safe rollback)."""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Reset all users to 'user' type
        cursor.execute("""
            UPDATE properties_userprofile
            SET user_type = 'user';
        """)
        print("Reset all users to 'user' type")


class Migration(migrations.Migration):
    dependencies = [
        ('properties', '0235_alter_activitylog_action'),
    ]

    operations = [
        migrations.RunPython(classify_user_types, reverse_classify_user_types),
    ]