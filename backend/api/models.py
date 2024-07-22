from django.db import models
from django.core.validators import (
    MinValueValidator,
    RegexValidator,
    MinLengthValidator,
)
from foodgram.const import (
    MIN_TIME_TO_COOK,
    MAX_LENGTH,
    MAX_LENGTH_TAG,
)
from django.contrib.auth import get_user_model

User = get_user_model()


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        verbose_name="Название",
        max_length=MAX_LENGTH_TAG,
        unique=True,
        blank=False,
    )
    slug = models.SlugField(
        verbose_name="Слаг",
        max_length=MAX_LENGTH_TAG,
        blank=False,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[-a-zA-Z0-9_]+$',
                message=("Использование только латинских букв, "
                         "цифр, подчеркивания и нижнего подчеркивания.")
            )
        ]
    )


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        verbose_name="Название",
        max_length=MAX_LENGTH,
        blank=False,
    )
    measurement_unit = models.CharField(
        verbose_name="Единица измерения",
        max_length=MAX_LENGTH,
        default='',
        blank=False,
    )


class Recipe(models.Model):
    """Модель рецепта."""

    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name="Ингредиенты",
        blank=False,
        through='RecipeToIngredient',
        related_name='ingredients'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name="Теги",
        blank=False,
        related_name='tags'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Aвтор",
        blank=False,
        related_name='recipe_author',
        default=1, # Убрать
    )
    image = models.ImageField(
        verbose_name="Фото",
        upload_to='food/images',
        blank=False,
    )
    name = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name="Название",
        blank=False,
    )
    text = models.TextField(
        verbose_name="Описание",
        max_length=MAX_LENGTH,
        blank=False,
    )
    cooking_time = models.IntegerField(
        verbose_name="Время приготовления",
        blank=False,
        validators=[
            MinValueValidator(MIN_TIME_TO_COOK)
        ]
    )


class RecipeToIngredient(models.Model):
    """Модель связи ингредиента и рецепта."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredientlist',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredientlist',
    )
    amount = models.PositiveSmallIntegerField(
        blank=False,
        default=1,
        validators=(
            MinValueValidator(1),), # вынести в конст
        verbose_name='Количество',
    )
