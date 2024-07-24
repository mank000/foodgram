from rest_framework.pagination import PageNumberPagination

from .models import Ingredient, Recipe, Tag
from .serializers import IngredientSerializer, RecipeSerializer, TagSerializer


class TagMixin:
    """Миксин для Тегов."""

    queryset = Tag.objects.all()
    pagination_class = None
    serializer_class = TagSerializer


class IngredientMixin:
    """Миксин для ингредиентов."""

    queryset = Ingredient.objects.all()
    pagination_class = None
    serializer_class = IngredientSerializer


class RecipeMixin:
    """Миксин для рецептов."""

    pagination_class = PageNumberPagination
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
