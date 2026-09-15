#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from django.core.management import call_command

# Fake the failing migration to skip it
call_command('migrate', 'properties', '0234', '--fake')
print("Migration 0234 faked successfully")
