
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

# Lister tous les utilisateurs
for user in User.objects.all():
    print(f"Username: {user.username}, Email: {user.email}")

# Choisir un utilisateur spécifique
user = User.objects.get(username='abdel')  # Remplacez 'john'

# Créer le token
token, created = Token.objects.get_or_create(user=user)
print(f"\nToken pour {user.username}: {token.key}")