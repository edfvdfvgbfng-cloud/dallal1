# Migration to create missing BrokerChannel table

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def create_brokerchannel_table(apps, schema_editor):
    """Create BrokerChannel table if it doesn't exist"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'properties_brokerchannel'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                CREATE TABLE properties_brokerchannel (
                    id BIGSERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    description TEXT DEFAULT '' NOT NULL,
                    category VARCHAR(100) DEFAULT 'general' NOT NULL,
                    governorate VARCHAR(100) DEFAULT '' NOT NULL,
                    status VARCHAR(20) DEFAULT 'active' NOT NULL,
                    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
                    is_featured BOOLEAN DEFAULT FALSE NOT NULL,
                    subscriber_count INTEGER DEFAULT 0 NOT NULL,
                    video_count INTEGER DEFAULT 0 NOT NULL,
                    post_count INTEGER DEFAULT 0 NOT NULL,
                    cover_image VARCHAR(200) DEFAULT '' NOT NULL,
                    profile_image VARCHAR(200) DEFAULT '' NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    broker_id INTEGER NULL,
                    UNIQUE (name, broker_id)
                );
            """)
            
            # Add foreign key
            try:
                cursor.execute("""
                    ALTER TABLE properties_brokerchannel 
                    ADD CONSTRAINT properties_brokerchannel_broker_id_fk 
                    FOREIGN KEY (broker_id) REFERENCES properties_broker(id) ON DELETE SET NULL;
                """)
            except Exception:
                pass


def reverse_migration(apps, schema_editor):
    """Reverse migration - drop BrokerChannel table"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS properties_brokerchannel CASCADE;")


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0228_fix_missing_schema'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(create_brokerchannel_table, reverse_migration),
    ]
