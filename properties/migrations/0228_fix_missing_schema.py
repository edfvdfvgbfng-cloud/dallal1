# Migration to fix missing schema after fake migrations
# This migration creates missing tables and columns that were not applied
# due to previous fake migration logic in entrypoint.sh

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0227_useronlinestatus_chatmessage_delivered_at_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Create SiteSettings table if it doesn't exist
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS properties_sitesettings (
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
            """,
            reverse_sql="DROP TABLE IF EXISTS properties_sitesettings CASCADE;"
        ),
        
        # Create Broker table if it doesn't exist
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS properties_broker (
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
            """,
            reverse_sql="DROP TABLE IF EXISTS properties_broker CASCADE;"
        ),
        
        # Create Office table if it doesn't exist
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS properties_office (
                    id BIGSERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    address VARCHAR(300) DEFAULT '' NOT NULL,
                    phone VARCHAR(30) DEFAULT '' NOT NULL,
                    governorate VARCHAR(100) DEFAULT '' NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    owner_id INTEGER NULL
                );
            """,
            reverse_sql="DROP TABLE IF EXISTS properties_office CASCADE;"
        ),
        
        # Add missing columns to properties_property if they don't exist
        migrations.RunSQL(
            sql="""
                ALTER TABLE properties_property 
                ADD COLUMN IF NOT EXISTS city VARCHAR(100) DEFAULT 'بغداد' NOT NULL;
            """,
            reverse_sql="ALTER TABLE properties_property DROP COLUMN IF EXISTS city;"
        ),
        
        migrations.RunSQL(
            sql="""
                ALTER TABLE properties_property 
                ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE NOT NULL;
            """,
            reverse_sql="ALTER TABLE properties_property DROP COLUMN IF EXISTS is_featured;"
        ),
        
        migrations.RunSQL(
            sql="""
                ALTER TABLE properties_property 
                ADD COLUMN IF NOT EXISTS is_promoted BOOLEAN DEFAULT FALSE NOT NULL;
            """,
            reverse_sql="ALTER TABLE properties_property DROP COLUMN IF EXISTS is_promoted;"
        ),
        
        migrations.RunSQL(
            sql="""
                ALTER TABLE properties_property 
                ADD COLUMN IF NOT EXISTS promotion_until DATE NULL;
            """,
            reverse_sql="ALTER TABLE properties_property DROP COLUMN IF EXISTS promotion_until;"
        ),
        
        migrations.RunSQL(
            sql="""
                ALTER TABLE properties_property 
                ADD COLUMN IF NOT EXISTS slug VARCHAR(220) DEFAULT '' NOT NULL;
            """,
            reverse_sql="ALTER TABLE properties_property DROP COLUMN IF EXISTS slug;"
        ),
        
        migrations.RunSQL(
            sql="""
                ALTER TABLE properties_property 
                ADD COLUMN IF NOT EXISTS title VARCHAR(200) DEFAULT '' NOT NULL;
            """,
            reverse_sql="ALTER TABLE properties_property DROP COLUMN IF EXISTS title;"
        ),
        
        migrations.RunSQL(
            sql="""
                ALTER TABLE properties_property 
                ADD COLUMN IF NOT EXISTS district VARCHAR(100) DEFAULT '' NOT NULL;
            """,
            reverse_sql="ALTER TABLE properties_property DROP COLUMN IF EXISTS district;"
        ),
        
        migrations.RunSQL(
            sql="""
                ALTER TABLE properties_property 
                ADD COLUMN IF NOT EXISTS province VARCHAR(30) DEFAULT 'baghdad' NOT NULL;
            """,
            reverse_sql="ALTER TABLE properties_property DROP COLUMN IF EXISTS province;"
        ),
        
        migrations.RunSQL(
            sql="""
                ALTER TABLE properties_property 
                ADD COLUMN IF NOT EXISTS latitude DECIMAL(9, 6) NULL;
            """,
            reverse_sql="ALTER TABLE properties_property DROP COLUMN IF EXISTS latitude;"
        ),
        
        migrations.RunSQL(
            sql="""
                ALTER TABLE properties_property 
                ADD COLUMN IF NOT EXISTS longitude DECIMAL(9, 6) NULL;
            """,
            reverse_sql="ALTER TABLE properties_property DROP COLUMN IF EXISTS longitude;"
        ),
        
        # Add foreign key columns if they don't exist
        migrations.RunSQL(
            sql="""
                ALTER TABLE properties_property 
                ADD COLUMN IF NOT EXISTS broker_id INTEGER NULL;
            """,
            reverse_sql="ALTER TABLE properties_property DROP COLUMN IF EXISTS broker_id;"
        ),
        
        migrations.RunSQL(
            sql="""
                ALTER TABLE properties_property 
                ADD COLUMN IF NOT EXISTS office_id INTEGER NULL;
            """,
            reverse_sql="ALTER TABLE properties_property DROP COLUMN IF EXISTS office_id;"
        ),
        
        migrations.RunSQL(
            sql="""
                ALTER TABLE properties_property 
                ADD COLUMN IF NOT EXISTS owner_id INTEGER NULL;
            """,
            reverse_sql="ALTER TABLE properties_property DROP COLUMN IF EXISTS owner_id;"
        ),
        
        # Add foreign key constraints
        migrations.RunSQL(
            sql="""
                ALTER TABLE properties_property 
                ADD CONSTRAINT IF NOT EXISTS properties_property_broker_id_fk 
                FOREIGN KEY (broker_id) REFERENCES properties_broker(id) ON DELETE SET NULL;
            """,
            reverse_sql="ALTER TABLE properties_property DROP CONSTRAINT IF EXISTS properties_property_broker_id_fk;"
        ),
        
        migrations.RunSQL(
            sql="""
                ALTER TABLE properties_property 
                ADD CONSTRAINT IF NOT EXISTS properties_property_office_id_fk 
                FOREIGN KEY (office_id) REFERENCES properties_office(id) ON DELETE SET NULL;
            """,
            reverse_sql="ALTER TABLE properties_property DROP CONSTRAINT IF EXISTS properties_property_office_id_fk;"
        ),
        
        migrations.RunSQL(
            sql="""
                ALTER TABLE properties_broker 
                ADD CONSTRAINT IF NOT EXISTS properties_broker_office_id_fk 
                FOREIGN KEY (office_id) REFERENCES properties_office(id) ON DELETE SET NULL;
            """,
            reverse_sql="ALTER TABLE properties_broker DROP CONSTRAINT IF EXISTS properties_broker_office_id_fk;"
        ),
        
        migrations.RunSQL(
            sql="""
                ALTER TABLE properties_broker 
                ADD CONSTRAINT IF NOT EXISTS properties_broker_parent_id_fk 
                FOREIGN KEY (parent_id) REFERENCES properties_broker(id) ON DELETE SET NULL;
            """,
            reverse_sql="ALTER TABLE properties_broker DROP CONSTRAINT IF EXISTS properties_broker_parent_id_fk;"
        ),
        
        migrations.RunSQL(
            sql="""
                ALTER TABLE properties_broker 
                ADD CONSTRAINT IF NOT EXISTS properties_broker_user_id_fk 
                FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE;
            """,
            reverse_sql="ALTER TABLE properties_broker DROP CONSTRAINT IF EXISTS properties_broker_user_id_fk;"
        ),
        
        # Add indexes
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS properties__provinc_14c1b1_idx 
                ON properties_property(province, city);
            """,
            reverse_sql="DROP INDEX IF EXISTS properties__provinc_14c1b1_idx;"
        ),
        
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS properties__type_d3d96a_idx 
                ON properties_property(type, status);
            """,
            reverse_sql="DROP INDEX IF EXISTS properties__type_d3d96a_idx;"
        ),
        
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS properties__price_32e7c2_idx 
                ON properties_property(price);
            """,
            reverse_sql="DROP INDEX IF EXISTS properties__price_32e7c2_idx;"
        ),
        
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS properties__created_9ef325_idx 
                ON properties_property(created_at DESC);
            """,
            reverse_sql="DROP INDEX IF EXISTS properties__created_9ef325_idx;"
        ),
        
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS properties__is_feat_b56ef4_idx 
                ON properties_property(is_featured, is_promoted);
            """,
            reverse_sql="DROP INDEX IF EXISTS properties__is_feat_b56ef4_idx;"
        ),
        
        # Add unique constraint on slug
        migrations.RunSQL(
            sql="""
                ALTER TABLE properties_property 
                ADD CONSTRAINT properties_property_slug_key UNIQUE (slug);
            """,
            reverse_sql="ALTER TABLE properties_property DROP CONSTRAINT IF EXISTS properties_property_slug_key;"
        ),
    ]
