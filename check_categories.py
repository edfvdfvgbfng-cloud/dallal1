#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from properties.models import JobCategory

print("=== Job Categories Check ===")

categories = JobCategory.objects.all()
print(f"Total categories: {categories.count()}")

for category in categories:
    print(f"- ID: {category.id}, Name: {category.name_ar}, Active: {category.is_active}")

active_categories = JobCategory.objects.filter(is_active=True)
print(f"\nActive categories: {active_categories.count()}")

if active_categories.count() == 0:
    print("\nNo active categories found. Creating sample categories...")
    
    JobCategory.objects.create(
        name_ar='تقنية المعلومات',
        name_en='Information Technology',
        icon='💻',
        description='وظائف في مجال البرمجة وتقنية المعلومات',
        is_active=True
    )
    
    JobCategory.objects.create(
        name_ar='الهندسة',
        name_en='Engineering',
        icon='⚙️',
        description='وظائف في مجال الهندسة المختلفة',
        is_active=True
    )
    
    JobCategory.objects.create(
        name_ar='المبيعات والتسويق',
        name_en='Sales and Marketing',
        icon='📊',
        description='وظائف في مجال المبيعات والتسويق',
        is_active=True
    )
    
    JobCategory.objects.create(
        name_ar='المحاسبة والمالية',
        name_en='Accounting and Finance',
        icon='💰',
        description='وظائف في مجال المحاسبة والمالية',
        is_active=True
    )
    
    JobCategory.objects.create(
        name_ar='التعليم',
        name_en='Education',
        icon='📚',
        description='وظائف في مجال التعليم',
        is_active=True
    )
    
    print("Created 5 sample categories successfully!")

print("\n=== Categories after update ===")
all_categories = JobCategory.objects.all()
for category in all_categories:
    print(f"- {category.name_en} (Active: {category.is_active})")
