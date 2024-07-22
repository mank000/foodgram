from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import FoodGrammUser

# Доделать сортировку по почте_






UserAdmin.fieldsets += (

    ('Extra Fields',
     {'fields': ('avatar', 'is_subscribed'), }),
)

admin.site.register(FoodGrammUser, UserAdmin)
