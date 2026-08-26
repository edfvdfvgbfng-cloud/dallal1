# Merge migration to resolve conflict between 0181 and 0190
# Both migrations are leaf nodes, this merges them into a single migration path

from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('properties', '0181_property_alley_property_block_property_house_number_and_more'),
        ('properties', '0190_travelpackage_created_by'),
    ]

    operations = [
        # This migration does nothing but merge the two conflicting branches
    ]