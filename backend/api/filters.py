import django_filters
from .models import Recipe
from django_filters import rest_framework as filters
from .models import Ingredient
from django.db.models import Count
from django.db.models import Q

class RecipeFilter(django_filters.FilterSet):
    is_favorited = django_filters.BooleanFilter(
        field_name='favorited_by__id',
        method='filter_is_favorited',
        required=False
    )
    is_in_shopping_cart = django_filters.BooleanFilter(
        field_name='shopping_cart__id',
        method='filter_is_in_shopping_cart',
        required=False
    )
    author = django_filters.NumberFilter(
        field_name='author__id',
        lookup_expr='exact',
        required=False
    )
    tags = django_filters.CharFilter(
        method='filter_by_tags',
        required=False
    )

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'author', 'tags']

    def filter_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(favorited_by=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_cart=self.request.user.shopping_cart)
        return queryset

    def filter_by_tags(self, queryset, name, value):
        if isinstance(value, list) and value:
            tags = [tag.strip() for tag in value if tag.strip()]

            # Создаем запрос для рецептов, содержащих все указанные теги
            query = Q()
            for tag in tags:
                query &= Q(tags__slug=tag)

            # Фильтруем рецепты по наличию всех тегов
            queryset = queryset.filter(query)

            # Аннотируем количество тегов у каждого рецепта и фильтруем по точному совпадению
            queryset = queryset.annotate(num_tags=Count('tags')).filter(
                num_tags=len(tags),
                tags__slug__in=tags
            ).distinct()
        return queryset


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']
