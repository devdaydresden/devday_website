from django.contrib.auth import get_user_model
import random
from string import ascii_letters, digits, punctuation

User = get_user_model()

PASSWORD_ALPHABET = ascii_letters + digits + punctuation


def generate_random_password():
    return "".join(random.choices(PASSWORD_ALPHABET, k=16))


def create_test_user(email='test@example.org', **kwargs):
    password = generate_random_password()
    return (
        User.objects.create_user(email=email, password=password, **kwargs),
        password)
