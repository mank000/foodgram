from collections import defaultdict
from io import BytesIO

import pyshorteners
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate
from rest_framework import status
from rest_framework.response import Response

from users.models import Subscribe
from .models import Recipe, RecipeToIngredient

DOT_SYMBOL = u'\u2022'


def generate_shopping_list(recipes):
    recipe_ids = [recipe.get('recipe_id') for recipe in recipes.values()]

    ingredient_data = RecipeToIngredient.objects.filter(
        recipe__in=recipe_ids).values(
        'ingredient__name', 'ingredient__measurement_unit'
    ).annotate(total_amount=Sum('amount'))

    ingredients_dict = defaultdict(lambda: defaultdict(int))

    for item in ingredient_data:
        name = item['ingredient__name']
        unit = item['ingredient__measurement_unit']
        amount = item['total_amount']
        ingredients_dict[name][unit] += amount

    formatted_ingredients = []

    for name, units in ingredients_dict.items():
        for unit, amount in units.items():
            ingredient_line = f'{DOT_SYMBOL} {name} {amount} {unit}\n'
            formatted_ingredients.append(ingredient_line)

    buffer = BytesIO()
    pdf_file = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    pdfmetrics.registerFont(TTFont('TimesNewRoman', 'Fonts/TimesNewRoman.ttf'))
    normal_style.fontName = 'TimesNewRoman'

    paragraphs = [
        Paragraph(line, normal_style) for line in formatted_ingredients
    ]
    pdf_file.build(paragraphs)
    buffer.seek(0)
    return buffer


def create_short_link(full_link):
    shortener = pyshorteners.Shortener()
    return shortener.tinyurl.short(full_link)


def get_recipes_for_serializer(self, obj):
    recipes = Recipe.objects.filter(author=obj)
    recipes_limit = self.context.get('recipes_limit')
    if recipes_limit is not None:
        try:
            recipes_limit = int(recipes_limit)
            recipes = recipes[:recipes_limit]
        except ValueError:
            return Response(
                {'Ошибка': 'Не правильно задано число limit'},
                status=status.HTTP_400_BAD_REQUEST
            )
    return recipes


def get_is_subscribet_for_serizlizer(self, obj):
    user = self.context.get('current_user')
    return Subscribe.objects.filter(
        user=user, author=obj.author
    ).exists() if user and user.is_authenticated else False


def add_recipe_to_list(model, user, recipe_id, serializer_class):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    item, created = model.objects.get_or_create(user=user, recipe=recipe)
    if created:
        serializer = serializer_class(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(
        {'detail': 'Этот рецепт уже в вашей коллекции.'},
        status=status.HTTP_400_BAD_REQUEST,
    )


def remove_recipe_from_list(model, user, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    item = model.objects.filter(user=user, recipe=recipe)
    if not item.exists():
        return Response(status=status.HTTP_400_BAD_REQUEST)
    item.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
