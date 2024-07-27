import csv
import os

from django.core.management.base import BaseCommand
from api.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт данных из CSV файла в базу данных'

    def handle(self, *args, **kwargs):
        base_dir = os.path.join('/app')
        csv_file_path = os.path.join(base_dir, 'data', 'ingredients.csv')

        with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)

            for row in csv_reader:
                try:
                    ingredient_name = row['name']
                    measurement_unit = row['measurement_unit']

                    Ingredient.objects.create(
                        name=ingredient_name,
                        measurement_unit=measurement_unit,
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Ошибка при сохранении ингредиента: {e}'
                        )
                    )
        self.stdout.write(self.style.SUCCESS('Данные успешно импортированы'))
