# Generated migration for performance optimization
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0218_make_property_fields_optional'),  # Latest migration
    ]

    operations = [
        # Add indexes for commonly searched fields
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['status'], name='idx_property_status'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['type'], name='idx_property_type'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['purpose'], name='idx_property_purpose'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['governorate'], name='idx_property_governorate'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['city'], name='idx_property_city'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['category'], name='idx_property_category'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['-created_at'], name='idx_property_created_at'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['is_featured'], name='idx_property_featured'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['is_verified'], name='idx_property_verified'),
        ),
        # Composite indexes for common filter combinations
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['status', 'created_at'], name='idx_property_status_created'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['governorate', 'city'], name='idx_property_location'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['type', 'purpose'], name='idx_property_type_purpose'),
        ),
        # Indexes for foreign key relationships
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['broker'], name='idx_property_broker'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['owner'], name='idx_property_owner'),
        ),
        # Indexes for PropertyImage
        migrations.AddIndex(
            model_name='propertyimage',
            index=models.Index(fields=['property', 'is_primary'], name='idx_property_image_primary'),
        ),
        migrations.AddIndex(
            model_name='propertyimage',
            index=models.Index(fields=['property', 'sort_order'], name='idx_property_image_sort'),
        ),
        # Indexes for HotelPage
        migrations.AddIndex(
            model_name='hotelpage',
            index=models.Index(fields=['status', 'created_at'], name='idx_hotel_status_created'),
        ),
        migrations.AddIndex(
            model_name='hotelpage',
            index=models.Index(fields=['governorate', 'city'], name='idx_hotel_location'),
        ),
        migrations.AddIndex(
            model_name='hotelpage',
            index=models.Index(fields=['page_type', 'is_outside_iraq'], name='idx_hotel_type_location'),
        ),
    ]

    operations = [
        # Add indexes for commonly searched fields
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['status'], name='idx_property_status'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['type'], name='idx_property_type'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['purpose'], name='idx_property_purpose'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['governorate'], name='idx_property_governorate'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['city'], name='idx_property_city'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['category'], name='idx_property_category'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['-created_at'], name='idx_property_created_at'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['is_featured'], name='idx_property_featured'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['is_verified'], name='idx_property_verified'),
        ),
        # Composite indexes for common filter combinations
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['status', 'created_at'], name='idx_property_status_created'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['governorate', 'city'], name='idx_property_location'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['type', 'purpose'], name='idx_property_type_purpose'),
        ),
        # Indexes for foreign key relationships
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['broker'], name='idx_property_broker'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=models.Index(fields=['owner'], name='idx_property_owner'),
        ),
        # Indexes for PropertyImage
        migrations.AddIndex(
            model_name='propertyimage',
            index=models.Index(fields=['property', 'is_primary'], name='idx_property_image_primary'),
        ),
        migrations.AddIndex(
            model_name='propertyimage',
            index=models.Index(fields=['property', 'sort_order'], name='idx_property_image_sort'),
        ),
        # Indexes for HotelPage
        migrations.AddIndex(
            model_name='hotelpage',
            index=models.Index(fields=['status', 'created_at'], name='idx_hotel_status_created'),
        ),
        migrations.AddIndex(
            model_name='hotelpage',
            index=models.Index(fields=['governorate', 'city'], name='idx_hotel_location'),
        ),
        migrations.AddIndex(
            model_name='hotelpage',
            index=models.Index(fields=['page_type', 'is_outside_iraq'], name='idx_hotel_type_location'),
        ),
    ]