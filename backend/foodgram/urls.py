from django.contrib import admin
from django.urls import path, include
from api.views import (
    AvatarView,
    GetTagsView,
    GetTagDetailView,
    GetIngredientsListView,
    GetIngredientDetailView,
    RecipeView,
    FavoriteView,
    ShoppingCartView,
    SubscribeView,
    SubscribeListView,
    GetRecipeView,
    GetRecipeLinkView,
    UserProfile
)

Tags = [
    path("", GetTagsView.as_view(), name="tag_list"),
    path("<int:id>/", GetTagDetailView.as_view(), name="get_tag"),
]

Ingredients = [
    path("", GetIngredientsListView.as_view(), name="ingredients_list"),
    path(
        "<int:id>/", GetIngredientDetailView.as_view(), name="get_ingredient"
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
    path("<int:id>/", GetRecipeView.as_view(), name="getrecipe"),
    path(
        "<int:id>/get-link/", GetRecipeLinkView.as_view(), name="getrecipelink"
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
