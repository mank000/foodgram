from django.test import TestCase

from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )
    avatar = models.ImageField(
        upload_to='images/users',
        verbose_name='Изображение'
    )

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'
