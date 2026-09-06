#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from django.db import connection

try:
    with connection.cursor() as cursor:
        # Drop all indexes on properties_property table that might conflict
        cursor.execute("DROP INDEX IF EXISTS properties_property_slug_f3b16024_like;")
        cursor.execute("DROP INDEX IF EXISTS properties__provinc_14c1b1_idx;")
        cursor.execute("DROP INDEX IF EXISTS properties__type_d3d96a_idx;")
        cursor.execute("DROP INDEX IF EXISTS properties__price_32e7c2_idx;")
        cursor.execute("DROP INDEX IF EXISTS properties__created_9ef325_idx;")
        cursor.execute("DROP INDEX IF EXISTS properties__is_feat_b56ef4_idx;")
        cursor.execute("DROP INDEX IF EXISTS properties__city_idx;")
        print("Successfully dropped all conflicting indexes")
except Exception as e:
    print(f"Could not drop indexes: {e}")
