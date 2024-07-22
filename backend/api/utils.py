from pathlib import Path

from users.models import ShoppingCart
from .models import RecipeToIngredient, Ingredient
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import pyshorteners

def generate_shopping_list(recipes):
    unique_ingredients = set()

    for recipe in recipes.values():
        recipe_ingredients = RecipeToIngredient.objects.all().filter(recipe=recipe.get('recipe_id'))

        for ingredient_mapping in recipe_ingredients.values():
            ingredient_details = []
            ingredient = Ingredient.objects.all().filter(id=ingredient_mapping.get('ingredient_id'))[0]
            ingredient_details.append(ingredient.name)
            ingredient_details.append(ingredient_mapping.get('amount'))
            ingredient_details.append(ingredient.measurement_unit)
            unique_ingredients.add(frozenset(ingredient_details))

    formatted_ingredients = []

    for ingredient_set in unique_ingredients:
        ingredient_line = [u"\u2022", "", "", "", "\n"]
        for item in ingredient_set:
            if isinstance(item, int):
                ingredient_line[2] = item
            elif isinstance(item, str) and len(item) > 3:
                ingredient_line[1] = item
            else:
                ingredient_line[3] = item
        formatted_line = " ".join(str(x) for x in ingredient_line)
        formatted_ingredients.append(formatted_line)
    
    pdf_path = Path("shopping_list.pdf")

    pdf_file = SimpleDocTemplate(str(pdf_path), pagesize=A4)

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    pdfmetrics.registerFont(TTFont('TimesNewRoman', "Fonts/TimesNewRoman.ttf"))
    normal_style.fontName = 'TimesNewRoman'

    paragraphs = [Paragraph(line, normal_style) for line in formatted_ingredients]
    pdf_file.build(paragraphs)
    return pdf_path.resolve()

def create_short_link(full_link):
    shortener = pyshorteners.Shortener()
    return shortener.tinyurl.short(full_link)