#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taji.settings')
django.setup()

from core.models import User

# Find the admin user and set their role to 'admin'
try:
    admin_user = User.objects.get(username='admin')
    admin_user.role = 'admin'
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.save()
    
    print("✅ Admin user role fixed!")
    print(f"Username: {admin_user.username}")
    print(f"Role: {admin_user.role}")
    print(f"Is Staff: {admin_user.is_staff}")
    print(f"Is Superuser: {admin_user.is_superuser}")
    
except User.DoesNotExist:
    print("❌ Admin user not found!")
    print("Available users:")
    for user in User.objects.all():
        print(f"  - {user.username} (role: {user.role})")