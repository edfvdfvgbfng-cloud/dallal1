# Migration to fix missing schema after fake migrations
# This migration creates missing tables and columns that were not applied
# due to previous fake migration logic in entrypoint.sh

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def create_missing_tables_and_columns(apps, schema_editor):
    """Create missing tables and columns safely"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Check and create SiteSettings table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'properties_sitesettings'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                CREATE TABLE properties_sitesettings (
                    id BIGSERIAL PRIMARY KEY,
                    site_name VARCHAR(100) DEFAULT 'دلال' NOT NULL,
                    tagline VARCHAR(200) DEFAULT '' NOT NULL,
                    favicon VARCHAR(200) DEFAULT '' NOT NULL,
                    logo VARCHAR(200) DEFAULT '' NOT NULL,
                    site_description TEXT DEFAULT '' NOT NULL,
                    default_language VARCHAR(10) DEFAULT 'ar' NOT NULL,
                    timezone VARCHAR(50) DEFAULT 'Asia/Baghdad' NOT NULL,
                    date_format VARCHAR(20) DEFAULT '%Y-%m-%d' NOT NULL,
                    time_format VARCHAR(20) DEFAULT '%H:%M' NOT NULL,
                    contact_email VARCHAR(254) DEFAULT '' NOT NULL,
                    contact_phone VARCHAR(30) DEFAULT '07701234567' NOT NULL,
                    contact_address VARCHAR(300) DEFAULT '' NOT NULL,
                    contact_city VARCHAR(100) DEFAULT '' NOT NULL,
                    contact_country VARCHAR(100) DEFAULT '' NOT NULL,
                    telegram_url VARCHAR(200) DEFAULT '' NOT NULL,
                    tiktok_url VARCHAR(200) DEFAULT '' NOT NULL,
                    youtube_url VARCHAR(200) DEFAULT '' NOT NULL,
                    snapchat_url VARCHAR(200) DEFAULT '' NOT NULL,
                    facebook_url VARCHAR(200) DEFAULT '' NOT NULL,
                    instagram_url VARCHAR(200) DEFAULT '' NOT NULL,
                    twitter_url VARCHAR(200) DEFAULT '' NOT NULL,
                    linkedin_url VARCHAR(200) DEFAULT '' NOT NULL,
                    whatsapp VARCHAR(30) DEFAULT '' NOT NULL,
                    about_title VARCHAR(200) DEFAULT 'من نحن' NOT NULL,
                    about_content TEXT DEFAULT '' NOT NULL,
                    mission TEXT DEFAULT '' NOT NULL,
                    broker_phone VARCHAR(30) DEFAULT '07701234567' NOT NULL,
                    broker_email VARCHAR(254) DEFAULT '' NOT NULL,
                    broker_address VARCHAR(300) DEFAULT '' NOT NULL,
                    maintenance_mode BOOLEAN DEFAULT FALSE NOT NULL,
                    maintenance_message TEXT DEFAULT '' NOT NULL,
                    maintenance_end_time TIMESTAMP WITH TIME ZONE NULL,
                    allow_admins_during_maintenance BOOLEAN DEFAULT TRUE NOT NULL
                );
            """)
        
        # Check and create Broker table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'properties_broker'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                CREATE TABLE properties_broker (
                    id BIGSERIAL PRIMARY KEY,
                    phone VARCHAR(20) NOT NULL,
                    office_name VARCHAR(200) DEFAULT '' NOT NULL,
                    governorate VARCHAR(100) DEFAULT '' NOT NULL,
                    role VARCHAR(10) DEFAULT 'sub' NOT NULL,
                    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    subscription_type VARCHAR(10) DEFAULT 'free' NOT NULL,
                    id_card_image VARCHAR(200) DEFAULT '' NOT NULL,
                    bio TEXT DEFAULT '' NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    office_id INTEGER NULL,
                    parent_id INTEGER NULL,
                    user_id INTEGER NOT NULL UNIQUE
                );
            """)
        
        # Check and create Office table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'properties_office'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                CREATE TABLE properties_office (
                    id BIGSERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    address VARCHAR(300) DEFAULT '' NOT NULL,
                    phone VARCHAR(30) DEFAULT '' NOT NULL,
                    governorate VARCHAR(100) DEFAULT '' NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    owner_id INTEGER NULL
                );
            """)
        
        # Check and add missing columns to properties_property
        columns_to_add = [
            ('city', 'VARCHAR(100)', 'بغداد'),
            ('is_featured', 'BOOLEAN', 'FALSE'),
            ('is_promoted', 'BOOLEAN', 'FALSE'),
            ('promotion_until', 'DATE', 'NULL'),
            ('slug', 'VARCHAR(220)', ''),
            ('title', 'VARCHAR(200)', ''),
            ('district', 'VARCHAR(100)', ''),
            ('province', 'VARCHAR(30)', 'baghdad'),
            ('latitude', 'DECIMAL(9,6)', 'NULL'),
            ('longitude', 'DECIMAL(9,6)', 'NULL'),
            ('broker_id', 'INTEGER', 'NULL'),
            ('office_id', 'INTEGER', 'NULL'),
            ('owner_id', 'INTEGER', 'NULL'),
        ]
        
        for col_name, col_type, default_val in columns_to_add:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'properties_property' 
                    AND column_name = %s
                );
            """, [col_name])
            if not cursor.fetchone()[0]:
                if default_val == 'NULL':
                    cursor.execute(f"""
                        ALTER TABLE properties_property 
                        ADD COLUMN {col_name} {col_type} NULL;
                    """)
                else:
                    cursor.execute(f"""
                        ALTER TABLE properties_property 
                        ADD COLUMN {col_name} {col_type} DEFAULT '{default_val}' NOT NULL;
                    """)
        
        # Add foreign key constraints
        try:
            cursor.execute("""
                ALTER TABLE properties_property 
                ADD CONSTRAINT properties_property_broker_id_fk 
                FOREIGN KEY (broker_id) REFERENCES properties_broker(id) ON DELETE SET NULL;
            """)
        except Exception:
            pass  # Constraint may already exist
        
        try:
            cursor.execute("""
                ALTER TABLE properties_property 
                ADD CONSTRAINT properties_property_office_id_fk 
                FOREIGN KEY (office_id) REFERENCES properties_office(id) ON DELETE SET NULL;
            """)
        except Exception:
            pass
        
        try:
            cursor.execute("""
                ALTER TABLE properties_broker 
                ADD CONSTRAINT properties_broker_office_id_fk 
                FOREIGN KEY (office_id) REFERENCES properties_office(id) ON DELETE SET NULL;
            """)
        except Exception:
            pass
        
        try:
            cursor.execute("""
                ALTER TABLE properties_broker 
                ADD CONSTRAINT properties_broker_parent_id_fk 
                FOREIGN KEY (parent_id) REFERENCES properties_broker(id) ON DELETE SET NULL;
            """)
        except Exception:
            pass
        
        try:
            cursor.execute("""
                ALTER TABLE properties_broker 
                ADD CONSTRAINT properties_broker_user_id_fk 
                FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE;
            """)
        except Exception:
            pass
        
        # Add indexes
        indexes = [
            'properties__provinc_14c1b1_idx ON properties_property(province, city)',
            'properties__type_d3d96a_idx ON properties_property(type, status)',
            'properties__price_32e7c2_idx ON properties_property(price)',
            'properties__created_9ef325_idx ON properties_property(created_at DESC)',
            'properties__is_feat_b56ef4_idx ON properties_property(is_featured, is_promoted)',
        ]
        
        for index_def in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_def}")
            except Exception:
                pass
        
        # Add unique constraint on slug
        try:
            cursor.execute("""
                ALTER TABLE properties_property 
                ADD CONSTRAINT properties_property_slug_key UNIQUE (slug);
            """)
        except Exception:
            pass


def reverse_migration(apps, schema_editor):
    """Reverse migration - drop tables and columns"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Drop tables
        cursor.execute("DROP TABLE IF EXISTS properties_sitesettings CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS properties_broker CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS properties_office CASCADE;")
        
        # Drop columns from properties_property
        columns_to_drop = [
            'city', 'is_featured', 'is_promoted', 'promotion_until', 'slug', 'title',
            'district', 'province', 'latitude', 'longitude', 'broker_id', 'office_id', 'owner_id'
        ]
        
        for col_name in columns_to_drop:
            try:
                cursor.execute(f"ALTER TABLE properties_property DROP COLUMN IF EXISTS {col_name};")
            except Exception:
                pass


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0227_useronlinestatus_chatmessage_delivered_at_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(create_missing_tables_and_columns, reverse_migration),
    ]
