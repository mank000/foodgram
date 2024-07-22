from django.db import models
from django.contrib.auth.models import AbstractUser
# from api.models import Recipe
from django.contrib.auth.models import BaseUserManager
from django.core.validators import RegexValidator
# Нужно ли это мне вообще??
class FoodGrammUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not username:
            raise ValueError('The Username field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user 

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)


class FoodGrammUser(AbstractUser):
    avatar = models.ImageField(
        upload_to='users/avatar/',
        verbose_name='Изображение'
    )

    email = models.EmailField(
        unique=True,
        blank=False,
    )

    username = models.CharField(
        unique=True,
        max_length=50, #
        verbose_name='Ник',
    )

    objects = FoodGrammUserManager()


class Subscribe(models.Model):
    user = models.ForeignKey(
        FoodGrammUser,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        FoodGrammUser,
        on_delete=models.CASCADE,
        related_name='subscribing',
        verbose_name='Автор'
    )

    class Meta:
        ordering = ['-id', ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_subscription'
            )
        ]
    verbose_name = 'Подписка'
    verbose_name_plural = 'Подписки'


class Favorite(models.Model):

    user = models.ForeignKey(
        FoodGrammUser,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Пользователь'
    )

    recipe = models.ForeignKey(
        'api.Recipe',
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт'
    )


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        FoodGrammUser,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        'api.Recipe',
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт'
    )
