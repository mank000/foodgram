from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.pagination import (LimitOffsetPagination,
                                       PageNumberPagination)
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Favorite, ShoppingCart, Subscribe
from .filters import IngredientFilter, RecipeFilter
from .models import Ingredient, Recipe, Tag
from .permissions import IsAuthenticatedOrAuthor
from .serializers import (AvatarSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeSerializer,
                          ShoppingCartSerializer, SubscribeSerializer,
                          TagSerializer, UserProfileSerializer,
                          UserProfileSerializerWithRecipes)
from .utils import (add_recipe_to_list, create_short_link,
                    generate_shopping_list, remove_recipe_from_list)

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


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    lookup_field = 'id'


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    pagination_class = None
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    lookup_field = 'id'


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = [IsAuthenticatedOrAuthor]
    pagination_class = PageNumberPagination


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
            return Response({'Корзина': 'Корзина пуста.'},
                            status=status.HTTP_200_OK)

        pdf_buffer = generate_shopping_list(recipes)
        response = FileResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.pdf"'
        )

        return response


class SubscribeViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
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
                page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(
            queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        user = request.user
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)
        if user == author:
            return Response(
                {'Подписка': 'Нельзя подписаться на самого себя!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription, created = Subscribe.objects.get_or_create(
            user=user, author=author)
        if created:
            serializer = SubscribeSerializer(
                author, context=self.get_serializer_context())
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(
            {'Подписка': 'Вы уже подписаны.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def destroy(self, request, *args, **kwargs):
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)
        subscription = Subscribe.objects.filter(
            user=request.user, author=author)
        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'Подписка': 'Вы не подписаны на данного пользователя.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['current_user'] = self.request.user
        return context


class GetRecipeLinkView(APIView):

    def get(self, request, id):
        return Response(
            {
                'short-link': create_short_link(
                    request.build_absolute_uri(f'/recipes/{id}/')
                )
            },
            status=status.HTTP_200_OK,
        )


class UserProfile(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user
