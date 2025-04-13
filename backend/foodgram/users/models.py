from django.db import models
from django.contrib.auth.models import AbstractUser

MAX_LENHT_NAME = 254
MAX_LENHT_USERNAME = 150
MAX_LENGHT_AVATAR = 255


class User(AbstractUser):
    email = models.EmailField(unique=True, max_length=MAX_LENHT_NAME)
    username = models.CharField(max_length=MAX_LENHT_USERNAME, unique=True)
    first_name = models.CharField(max_length=MAX_LENHT_USERNAME)
    last_name = models.CharField(max_length=MAX_LENHT_USERNAME)
    avatar = models.ImageField(upload_to='avatars/', null=True,
                               blank=True,
                               max_length=MAX_LENGHT_AVATAR)

    def __str__(self):
        return self.username
