import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from api.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт данных из CSV файла в базу данных'

    def handle(self, *args, **kwargs):
        base_dir = os.path.dirname(settings.BASE_DIR)
        csv_file = os.path.join(base_dir, 'data', 'ingredients.csv')
        with open(csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            a = next(iter(reader))

            try:
                Ingredient.objects.create(
                    name=list(a.keys())[0],
                    measurement_unit=list(a.keys())[1],
                )
                Ingredient.objects.create(
                    name=list(a.values())[0],
                    measurement_unit=list(a.values())[1],
                )
            except Exception as e:
                self.stdout.write(f'Ошибка при сохранении: {e}')

            for row in reader:
                try:
                    Ingredient.objects.create(
                        name=list(row.values())[0],
                        measurement_unit=list(row.values())[1],
                    )
                except Exception:
                    Ingredient.objects.create(
                        name=list(row.values())[0],
                        measurement_unit='',
                    )

        self.stdout.write(self.style.SUCCESS('Данные успешно импортированы'))
