from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins, permissions, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Favorite, FoodGrammUser, ShoppingCart, Subscribe
from .filters import IngredientFilter, RecipeFilter
from .mixins import IngredientMixin, RecipeMixin, TagMixin
from .models import Ingredient, Recipe, RecipeToIngredient
from .serializers import (AvatarSerializer, FavoriteSerializer,
                          ShoppingCartSerializer, SubscribeSerializer,
                          UserProfileSerializer,
                          UserProfileSerializerWithRecipes)
from .utils import (create_short_link, generate_shopping_list,
                    add_recipe_to_list, remove_recipe_from_list)


User = get_user_model()


class AvatarView(APIView):
    """Работа с аватарами пользователей."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AvatarSerializer

    def put(self, request, *args, **kwargs):
        serializer = AvatarSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        user = request.user
        user.avatar.delete()
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetTagsView(TagMixin, generics.ListAPIView):
    """Получение тегов."""

    pass


class GetTagDetailView(TagMixin, generics.RetrieveAPIView):
    """Получение детальной информации о теге."""

    lookup_field = "id"


class GetIngredientsListView(IngredientMixin, generics.ListAPIView):
    """Получение списка ингредиентов."""

    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class GetIngredientDetailView(IngredientMixin, generics.RetrieveAPIView):
    """Получение списка ингредиентов."""

    lookup_field = "id"


class RecipeView(RecipeMixin, generics.ListCreateAPIView):

    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return Response(
                {"detail": "требуется аутентификация"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GetRecipeView(
    RecipeMixin,
    generics.RetrieveAPIView,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    permission_classes = [permissions.AllowAny]
    lookup_field = "id"

    def patch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "требуется аутентификация"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return self.partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer_data = serializer.validated_data

        ingredients = serializer_data.pop("ingredients")
        tags = serializer_data.pop("tags")

        recipe = get_object_or_404(Recipe, id=kwargs.get("id"))
        if user != recipe.author:
            return Response(status=status.HTTP_403_FORBIDDEN)

        tags = serializer_data.get("tags", [])
        for tag in tags:
            recipe.tags.add(tag)
        recipe.save()

        recipeingredients = RecipeToIngredient.objects.filter(recipe=recipe)
        for ingredient in ingredients:
            ingredient_id = ingredient.get("id")
            ingredient_obj = get_object_or_404(
                Ingredient.objects.all(), pk=ingredient_id
            )
            amount = ingredient.get("amount")

            isthereingredient = recipeingredients.filter(
                ingredient=ingredient_obj
            )

            if isthereingredient.exists():
                item = isthereingredient.first()
                item.amount += amount
                item.save()
            else:
                RecipeToIngredient.objects.create(
                    recipe=recipe, ingredient=ingredient_obj, amount=amount
                )
        response_serilizer = self.get_serializer(recipe)
        return Response(response_serilizer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "требуется аутентификация"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        recipe = get_object_or_404(Recipe, id=kwargs.get("id"))
        user = request.user
        author = recipe.author
        if user == author:
            return self.destroy(request, *args, **kwargs)
        return Response(status=status.HTTP_403_FORBIDDEN)


class FavoriteView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        return add_recipe_to_list(
            Favorite, request.user, id, FavoriteSerializer
        )

    def delete(self, request, id):
        return remove_recipe_from_list(Favorite, request.user, id)


class ShoppingCartView(APIView, mixins.DestroyModelMixin):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        return add_recipe_to_list(
            ShoppingCart, request.user, id, ShoppingCartSerializer
        )

    def delete(self, request, id):
        return remove_recipe_from_list(ShoppingCart, request.user, id)

    def get(self, request):
        user = request.user
        recipes = ShoppingCart.objects.filter(user=user)

        if not recipes.exists():
            return Response({"Корзина": "Корзина пуста."},
                            status=status.HTTP_200_OK)

        pdf_buffer = generate_shopping_list(recipes)
        response = FileResponse(pdf_buffer, content_type="application/pdf")
        response["Content-Disposition"] = (
            'attachment; filename="shopping_list.pdf"'
        )

        return response


class SubscribeView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)
        if user == author:
            return Response(
                {"Подписка": "Нельзя подписаться на самого себя!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription, created = Subscribe.objects.get_or_create(
            user=user, author=author
        )
        if created:
            serializer = SubscribeSerializer(
                author,
                context=self.get_serializer_context(),
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(
            {"Подписка": "Вы уже подписаны."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, id):
        author = get_object_or_404(FoodGrammUser, id=id)
        cart_recipe = Subscribe.objects.filter(
            user=request.user, author=author
        )
        if not cart_recipe.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        cart_recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['current_user'] = self.request.user
        return context


class SubscribeListView(generics.ListAPIView):

    permission_classes = [permissions.IsAuthenticated]

    serializer_class = UserProfileSerializerWithRecipes

    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        return User.objects.filter(subscribing__user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)


class GetRecipeLinkView(APIView):

    def get(self, request, id):
        return Response(
            {
                "short-link": create_short_link(
                    request.build_absolute_uri(f"/recipes/{id}/")
                )
            },
            status=status.HTTP_200_OK,
        )


class UserProfile(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user
