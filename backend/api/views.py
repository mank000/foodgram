from rest_framework import generics, permissions
from rest_framework.response import Response
from django.http import FileResponse
from rest_framework import status
from .serializers import (
    AvatarSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    SubscibeSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer,
    UserProfileSerializerWithRecipes,
    UserProfileSerializer
)
from rest_framework.views import APIView
from .models import Tag, Ingredient, Recipe, RecipeToIngredient
from rest_framework import mixins
from django.contrib.auth import get_user_model
from users.models import Favorite, ShoppingCart, Subscribe
from .utils import generate_shopping_list, create_short_link
from rest_framework.pagination import LimitOffsetPagination

from django.shortcuts import get_object_or_404
from .filters import RecipeFilter, IngredientFilter
from django_filters.rest_framework import DjangoFilterBackend
from users.models import FoodGrammUser

User = get_user_model()


class AvatarView(APIView):
    """Работа с аватарами пользователей."""

    # Работает если удалить с одного пользователя аватар другого?

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AvatarSerializer

    def put(self, request, *args, **kwargs):
        user = request.user

        serializer = AvatarSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            if not request.data:
                return Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        user = request.user
        user.avatar.delete()
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetTagsView(generics.ListAPIView):
    """Получение тегов."""

    queryset = Tag.objects.all()
    pagination_class = None
    serializer_class = TagSerializer


class GetTagDetailView(generics.RetrieveAPIView):
    """Получение детальной информации о теге."""

    queryset = Tag.objects.all()
    pagination_class = None
    serializer_class = TagSerializer
    lookup_field = "id"


class GetIngredientsListView(generics.ListAPIView):
    """Получение списка ингредиентов."""

    queryset = Ingredient.objects.all()
    pagination_class = None
    serializer_class = IngredientSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class GetIngredientDetailView(generics.RetrieveAPIView):
    """Получение списка ингредиентов."""

    queryset = Ingredient.objects.all()
    pagination_class = None
    serializer_class = IngredientSerializer
    lookup_field = "id"


class RecipeView(generics.ListCreateAPIView):

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    # filterset_fields = ('author', 'tags', 'is_in_shopping_cart')

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Аутентификация требуется"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer_data = serializer.validated_data

        ingredients = serializer_data.pop("ingredients")
        tags = serializer_data.pop("tags")

        # Make recipe

        recipe = Recipe.objects.create(**serializer_data, author=request.user)
        recipe.tags.set(tags)

        # Make RecipeToIngredient

        for ingredient in ingredients:
            ingredient_id = ingredient.get("id")
            ingredient_obj = get_object_or_404(
                Ingredient.objects.all(), pk=ingredient_id
            )
            amount = ingredient.get("amount")

            RecipeToIngredient.objects.create(
                recipe=recipe, ingredient=ingredient_obj, amount=amount
            )
        response_serializer = self.get_serializer(recipe)
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED
        )


class GetRecipeView(
    generics.RetrieveAPIView, mixins.UpdateModelMixin, mixins.DestroyModelMixin
):

    permission_classes = [permissions.AllowAny]  # ?
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
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

        # Находим рецепт

        recipe = get_object_or_404(Recipe, id=kwargs.get("id"))
        if user != recipe.author:
            return Response(status=status.HTTP_403_FORBIDDEN)
        # Добавляем теги

        tags = serializer_data.get("tags", [])
        for tag in tags:
            recipe.tags.add(tag)
        recipe.save()

        # Создаем связь рецепт-ингедиент

        RecipeIngredients = RecipeToIngredient.objects.filter(recipe=recipe)
        for ingredient in ingredients:
            ingredient_id = ingredient.get("id")
            ingredient_obj = get_object_or_404(
                Ingredient.objects.all(), pk=ingredient_id
            )
            amount = ingredient.get("amount")

            IsThereIngredient = RecipeIngredients.filter(
                ingredient=ingredient_obj
            )

            if IsThereIngredient.exists():
                item = IsThereIngredient.first()
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
        user = request.user
        recipe = generics.get_object_or_404(Recipe, id=id)
        favorite, created = Favorite.objects.get_or_create(
            user=user, recipe=recipe
        )

        if created:
            return Response(
                FavoriteSerializer(favorite).data,
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"detail": "This recipe is already in your favorites."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request, id):
        user = request.user
        recipe = get_object_or_404(Recipe, id=id)
        favorite = Favorite.objects.filter(user=user, recipe=recipe)
        if not favorite.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartView(APIView, mixins.DestroyModelMixin):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        user = request.user
        recipe = get_object_or_404(Recipe, id=id)

        cart_recipe, created = ShoppingCart.objects.get_or_create(
            user=user, recipe=recipe
        )

        if created:
            serializer = ShoppingCartSerializer(cart_recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:  # зименеить подиись
            return Response(
                {"detail": "Этот рецепт уже в вашей корзине."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request, id):

        user = request.user
        recipe = Recipe.objects.filter(id=id)

        if not recipe.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        cart_recipe = ShoppingCart.objects.filter(
            user=user, recipe=recipe.first()
        )

        if not cart_recipe.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        cart_recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get(self, request):
        user = request.user

        recipes = ShoppingCart.objects.filter(user=user)
        if not recipes.exists():
            return Response({"Корзина": "Корзина пуста."})
        path = generate_shopping_list(recipes)
        pdf_file = open(path, 'rb')
        response = FileResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{pdf_path.name}"'
        

        return Response(response, status=status.HTTP_204_NO_CONTENT)

        file = ...


class SubscribeView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        # проверка на подписку самого на себя

        user = request.user
        author = get_object_or_404(User, id=id)
        if user == author:
            return Response(
                {"Подписка": "Нельзя подпиаться на самого себя!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cart_recipe, created = Subscribe.objects.get_or_create(
            user=user, author=author
        )
        if created:
            recipes_limit = request.query_params.get("recipes_limit")
            if recipes_limit is not None:
                try:
                    recipes_limit = int(recipes_limit)
                except ValueError:
                    recipes_limit = None
            else:
                recipes_limit = None
            return Response(
                SubscibeSerializer(
                    author,
                    context={
                        "request": request,
                        "recipes_limit": recipes_limit,
                    },
                ).data,
                status=status.HTTP_201_CREATED,
            )
        else:  # зименеить подиись
            return Response(
                {"detail": "This recipe is already in your favorites."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request, id):
        user = request.user
        author = get_object_or_404(FoodGrammUser, id=id)
        cart_recipe = Subscribe.objects.filter(user=user, author=author)
        if not cart_recipe.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # cart_recipe = get_object_or_404(Subscribe, user=user, author=author

        cart_recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
                    request.build_absolute_uri(f"/api/recipes/{id}/")
                )
            },
            status=status.HTTP_200_OK,
        )


class UserProfile(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user
