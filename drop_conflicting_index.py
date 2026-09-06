#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from django.db import connection

try:
    with connection.cursor() as cursor:
        cursor.execute("DROP INDEX IF EXISTS properties_property_slug_f3b16024_like;")
        print("Successfully dropped conflicting index")
except Exception as e:
    print(f"Could not drop index: {e}")
