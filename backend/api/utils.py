from collections import defaultdict
from pathlib import Path

import pyshorteners
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate

from .models import Ingredient, RecipeToIngredient

DOT_SYMBOL = u'\u2022'


def generate_shopping_list(recipes):
    ingredients_dict = defaultdict(lambda: defaultdict(int))

    for recipe in recipes.values():
        recipe_ingredients = RecipeToIngredient.objects.all().filter(
            recipe=recipe.get('recipe_id')
        )

        for ingredient_mapping in recipe_ingredients.values():
            ingredient = Ingredient.objects.get(
                id=ingredient_mapping.get('ingredient_id')
            )
            name = ingredient.name
            unit = ingredient.measurement_unit
            amount = ingredient_mapping.get('amount')

            ingredients_dict[name][unit] += amount

    formatted_ingredients = []

    for name, units in ingredients_dict.items():
        for unit, amount in units.items():
            ingredient_line = f"{DOT_SYMBOL} {name} {amount} {unit}\n"
            formatted_ingredients.append(ingredient_line)

    pdf_path = Path("shopping_list.pdf")
    pdf_file = SimpleDocTemplate(str(pdf_path), pagesize=A4)

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    pdfmetrics.registerFont(TTFont('TimesNewRoman', "Fonts/TimesNewRoman.ttf"))
    normal_style.fontName = 'TimesNewRoman'

    paragraphs = [
        Paragraph(line, normal_style) for line in formatted_ingredients
    ]
    pdf_file.build(paragraphs)
    return pdf_path.resolve()


def create_short_link(full_link):
    shortener = pyshorteners.Shortener()
    return shortener.tinyurl.short(full_link)
