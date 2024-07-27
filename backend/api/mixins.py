from .models import Ingredient
from .serializers import IngredientSerializer


class IngredientMixin:
    """Миксин для ингредиентов."""

    queryset = Ingredient.objects.all()
    pagination_class = None
    serializer_class = IngredientSerializer
