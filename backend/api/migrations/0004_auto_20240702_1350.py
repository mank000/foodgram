# Generated by Django 3.2.16 on 2024-07-02 06:50

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_rename_title_tag_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ingredient',
            old_name='title',
            new_name='name',
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(max_length=32, unique=True, verbose_name='Название'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='slug',
            field=models.SlugField(max_length=32, unique=True, validators=[django.core.validators.RegexValidator(message='Использование только латинских букв, цифр, подчеркивания и нижнего подчеркивания.', regex='^[-a-zA-Z0-9_]+$')], verbose_name='Слаг'),
        ),
    ]
