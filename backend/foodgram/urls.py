from django.contrib import admin
from django.urls import include, path

from api.views import (AvatarView, FavoriteView, GetIngredientDetailView,
                       GetIngredientsListView, GetRecipeLinkView,
                       GetRecipeView, GetTagDetailView, GetTagsView,
                       RecipeView, ShoppingCartView, SubscribeListView,
                       SubscribeView, UserProfile)

Tags = [
    path("", GetTagsView.as_view(), name="tag-list"),
    path("<int:id>/", GetTagDetailView.as_view(), name="get-tag"),
]

Ingredients = [
    path("", GetIngredientsListView.as_view(), name="ingredients-list"),
    path(
        "<int:id>/", GetIngredientDetailView.as_view(), name="get-ingredient"
    ),
]


Users = [
    path("me/avatar/", AvatarView.as_view(), name="avatars"),
    path("subscriptions/", SubscribeListView.as_view(), name="subscritions"),
    path("<int:id>/subscribe/", SubscribeView.as_view(), name="subscribe"),
    path("me/", UserProfile.as_view(), name="user-me")
]

Recipes = [
    path(
        "<int:id>/shopping_cart/",
        ShoppingCartView.as_view(),
        name="favorite-recipe",
    ),
    path(
        "download_shopping_cart/",
        ShoppingCartView.as_view(),
        name="download_cart",
    ),
    path("<int:id>/favorite/", FavoriteView.as_view(), name="favorite-recipe"),
    path("", RecipeView.as_view(), name="recipe"),
    path("<int:id>/", GetRecipeView.as_view(), name="get-recipe"),
    path(
        "<int:id>/get-link/",
        GetRecipeLinkView.as_view(),
        name="get-recipe-link"
    ),
]

Api = [
    path("users/", include(Users)),
    path("tags/", include(Tags)),
    path("ingredients/", include(Ingredients)),
    path("recipes/", include(Recipes)),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
]


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(Api)),
]
