#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taji.settings')
django.setup()

from core.models import User

# Create admin user if it doesn't exist
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@taji.com',
        password='admin123',
        first_name='Admin',
        last_name='User',
        phone='0700000000',
        role='admin'
    )
    print("✅ Admin user created successfully!")
    print("Username: admin")
    print("Password: admin123")
else:
    print("ℹ️ Admin user already exists")