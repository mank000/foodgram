from django.contrib import admin
from django.urls import include, path

from api.views import (AvatarView, FavoriteView, GetRecipeLinkView,
                       IngredientViewSet, RecipeViewSet, ShoppingCartView,
                       SubscribeViewSet, TagViewSet, UserProfile)

Tags = [
    path('', TagViewSet.as_view({'get': 'list'}), name='tag-list'),
    path('<int:id>/', TagViewSet.as_view({'get': 'retrieve'}), name='get-tag'),

]

Ingredients = [
    path('', IngredientViewSet.as_view({
        'get': 'list'
    }), name='ingredients-list'),
    path(
        '<int:id>/', IngredientViewSet.as_view({
            'get': 'retrieve'
        }), name='get-ingredient'
    ),
]


Users = [
    path('me/avatar/', AvatarView.as_view(), name='avatars'),
    path('subscriptions/', SubscribeViewSet.as_view({'get': 'list'})),
    path('<int:id>/subscribe/',
         SubscribeViewSet.as_view({'post': 'create', 'delete': 'destroy'})),
    path('me/', UserProfile.as_view(), name='user-me')
]

Recipes = [
    path(
        '<int:id>/shopping_cart/',
        ShoppingCartView.as_view(),
        name='favorite-recipe',
    ),
    path(
        'download_shopping_cart/',
        ShoppingCartView.as_view(),
        name='download_cart',
    ),
    path('<int:id>/favorite/', FavoriteView.as_view(), name='favorite-recipe'),
    path(
        '<int:id>/get-link/',
        GetRecipeLinkView.as_view(),
        name='get-recipe-link'
    ),
    path('',
         RecipeViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='recipe-list-create'),
    path('<int:pk>/',
         RecipeViewSet.as_view(
             {'get': 'retrieve',
              'put': 'update',
              'patch': 'update',
              'delete': 'destroy'}),
         name='recipe-detail'),
]

Api = [
    path('users/', include(Users)),
    path('tags/', include(Tags)),
    path('ingredients/', include(Ingredients)),
    path('recipes/', include(Recipes)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(Api)),
]
