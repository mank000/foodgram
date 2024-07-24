from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from foodgram.const import MAX_LENGTH, MAX_LENGTH_TAG, MIN_TIME_TO_COOK

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
                regex=r"^[-a-zA-Z0-9_]+$",
                message=(
                    "Использование только латинских букв, "
                    "цифр, подчеркивания и нижнего подчеркивания."
                ),
            )
        ],
    )

    def __str__(self):
        return self.name


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
        default="",
        blank=False,
    )

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""

    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name="Ингредиенты",
        blank=False,
        through="RecipeToIngredient",
        related_name="ingredients",
    )
    tags = models.ManyToManyField(
        Tag, verbose_name="Теги", blank=False, related_name="tags"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Aвтор",
        blank=False,
        related_name="recipe_author",
    )
    image = models.ImageField(
        verbose_name="Фото",
        upload_to="food/images",
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
        validators=[MinValueValidator(MIN_TIME_TO_COOK)],
    )
    pub_date = models.DateTimeField(
        "Дата публикации",
        auto_now_add=True,
    )

    class Meta:
        ordering = ("-pub_date",)

    def __str__(self):
        return self.name


class RecipeToIngredient(models.Model):
    """Модель связи ингредиента и рецепта."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredientlist",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="ingredientlist",
    )
    amount = models.PositiveSmallIntegerField(
        blank=False,
        default=1,
        validators=(MinValueValidator(MIN_TIME_TO_COOK),),
        verbose_name="Количество",
    )
