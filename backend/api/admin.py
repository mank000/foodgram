from django.contrib import admin

from .models import Ingredient, Recipe, Tag


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Класс Администрации для ингредиентов."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Класс Администрации для тегов."""

    list_display = ('name', 'slug')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Класс Администрации для рецептов."""

    list_display = ('name', 'author')
    search_fields = ('name', 'author__username')
    list_filter = ('tags__name',)
