from django.contrib.auth.models import AbstractUser
from django.db import models

from foodgram.const import MAX_LENGTH_USER_NAME


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
        max_length=MAX_LENGTH_USER_NAME,
        verbose_name='Ник',
    )

    def __str__(self):
        return self.username


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
        related_name='favorites',
        verbose_name='Пользователь'
    )

    recipe = models.ForeignKey(
        'api.Recipe',
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт'
    )

    class Meta:
        unique_together = ['user', 'recipe']


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

    class Meta:
        unique_together = ['user', 'recipe']
