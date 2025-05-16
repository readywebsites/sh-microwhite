# myapp/auth_backends.py

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
# from django.core.exceptions import ObjectDoesNotExist

class CustomBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Authenticate the user based on the backend logic
        if username:
            try:
                user = User.objects.get(username=username)
                if user.check_password(password):
                    # Set the backend attribute on the user
                    user.backend = 'ecommerce.auth_backends.CustomBackend'
                    return user
            except User.DoesNotExist:
                return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None