import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pizzeria_saas.settings')
django.setup()

from accounts.models import User

user = User.objects.filter(username='Admin').first()
if user:
    user.set_password('Loli123.-')
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print(f"Password reset OK for Admin (id={user.id}, superuser={user.is_superuser})")
else:
    user = User.objects.create_superuser('Admin', 'admin@gastro-saas.com', 'Loli123.-')
    print(f"Created Admin (id={user.id})")

print(f"Total users: {User.objects.count()}")