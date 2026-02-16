
#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

print("🔍 Vérification des Tokens\n")

users = User.objects.all()
print(f"👥 Utilisateurs : {users.count()}")

for user in users:
    try:
        token = Token.objects.get(user=user)
        print(f"   ✅ {user.username} : {token.key}")
    except Token.DoesNotExist:
        print(f"   ❌ {user.username} : Pas de token")
        print(f"      → Créer avec : Token.objects.create(user=User.objects.get(username='{user.username}'))")

print("\n📋 Pour créer un token :")
print("   python manage.py shell")
print("   >>> from django.contrib.auth.models import User")
print("   >>> from rest_framework.authtoken.models import Token")
print("   >>> user = User.objects.first()")
print("   >>> token, _ = Token.objects.get_or_create(user=user)")
print("   >>> print(f'Token: {token.key}')")