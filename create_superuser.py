#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pizzeria_saas.settings')
django.setup()

from accounts.models import User

# Crear superuser
username = 'Admin'
email = 'admin@gastro-saas.com'
password = 'Loli123.-'

if User.objects.filter(username=username).exists():
    print(f"Usuario '{username}' ya existe")
    user = User.objects.get(username=username)
    print(f"Email: {user.email}")
    print(f"Superuser: {'Si' if user.is_superuser else 'No'}")
else:
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    print(f"Superuser '{username}' creado exitosamente")
    print(f"Email: {email}")
    print(f"Password: {password}")
    
print(f"\nAcceder en: http://127.0.0.1:8000/admin/")
print(f"Usuario: {username}")
print(f"Password: {password}")