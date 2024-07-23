from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Favorite, FoodGrammUser, ShoppingCart, Subscribe


class CustomUserAdmin(UserAdmin):
    search_fields = ('username', 'email')
    list_filter = ('username', 'email')
    list_display = ('username', 'email')

    fieldsets = UserAdmin.fieldsets + (
        ('Extra Fields', {
            'fields': ('avatar', ),
        }),
    )

    def get_queryset(self, request):
        return FoodGrammUser.objects.only('username', 'email')


admin.site.register(FoodGrammUser, CustomUserAdmin)


@admin.register(Favorite)
class Favorite(admin.ModelAdmin):
    list_display = ('pk',)


@admin.register(ShoppingCart)
class ShoppingCart(admin.ModelAdmin):
    list_display = ('pk',)


@admin.register(Subscribe)
class Subscribe(admin.ModelAdmin):
    list_display = ('pk',)
