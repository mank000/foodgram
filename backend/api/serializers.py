import re

from django.contrib.auth import get_user_model
from django.db.models import F
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from foodgram.const import MAX_LENGTH_EMAIL, MAX_LENGTH_SERIALIZERS
from users.models import Favorite, ShoppingCart, Subscribe
from .fields import Base64ImageField
from .models import Ingredient, Recipe, RecipeToIngredient, Tag
from .utils import get_is_subscribet_for_serizlizer, get_recipes_for_serializer

User = get_user_model()


class UserCreateSerializer(UserCreateSerializer):
    """Кастомные поля для регистарции."""

    email = serializers.EmailField(
        required=True,
        max_length=MAX_LENGTH_EMAIL,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='Пользователь с таким email уже существует.',
            )
        ],
    )

    username = serializers.CharField(
        required=True,
        max_length=MAX_LENGTH_SERIALIZERS,
    )

    first_name = serializers.CharField(
        required=True,
        max_length=MAX_LENGTH_SERIALIZERS,
    )

    last_name = serializers.CharField(
        required=True,
        max_length=MAX_LENGTH_SERIALIZERS,
    )

    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True,
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )

    def validate_username(self, value):
        """Валидация имени пользователя."""
        if not re.match(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError('Выберите другой ник')
        return value


class UserProfileSerializer(UserCreateSerializer):
    """Сериализатор профиля пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscribe.objects.filter(user=user, author=obj).exists()

    def to_representation(self, instance):

        if instance.is_anonymous:
            representation = super().to_representation(instance)
            representation.pop('email', None)
            return representation
        return super().to_representation(instance)


class UserProfileSerializerWithRecipes(serializers.ModelSerializer):

    recipes = serializers.SerializerMethodField()

    recipes_count = serializers.SerializerMethodField()

    is_subscribed = serializers.SerializerMethodField()

    class Meta:

        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_recipes(self, obj):
        recipes = get_recipes_for_serializer(self, obj)
        return RecipeShortReadSerializer(
            recipes, many=True, context=self.context
        ).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    def get_is_subscribed(self, obj):
        return get_is_subscribet_for_serizlizer(self, obj)


class AvatarSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(
        required=True,
    )

    class Meta:
        model = User
        fields = [
            'avatar',
        ]
        extra_kwargs = {
            'avatar': {'allow_null': False}
        }


class UserListProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
        )


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField()

    class Meta:
        model = RecipeToIngredient
        fields = (
            'id',
            'amount',
        )


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField(required=True, allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate_ingredients(self, value):
        if not value:
            raise ValidationError('Нужен хотя бы один ингредиент!')

        ingredients_set = set()

        for ingredient_data in value:
            ingredient_id = ingredient_data.get('id')
            ingredient_amount = ingredient_data.get('amount')

            if ingredient_id is None:
                raise ValidationError('ID ингредиента не может быть пустым!')

            try:
                Ingredient.objects.get(id=ingredient_id)
            except Exception:
                raise ValidationError(
                    f'Ингредиент с ID {ingredient_id} не найден!'
                )

            if ingredient_id in ingredients_set:
                raise ValidationError('Ингредиенты не должны повторяться!')

            ingredients_set.add(ingredient_id)

            if ingredient_amount is None or ingredient_amount <= 0:
                raise ValidationError(
                    'Количество ингредиента должно быть больше 0!'
                )

        return value

    def validate_tags(self, value):
        if len(value) == 0:
            raise ValidationError('Нужен хотя бы один тег!')
        tag_list = []
        for val in value:
            if val in tag_list:
                raise ValidationError('Тег не должен повторятся!')
            tag_list.append(val)
        return value

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data

    def create(self, validated_data):
        request = self.context['request']
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=request.user, **validated_data)

        if tags_data:
            recipe.tags.set(tags_data)

        if ingredients_data:
            recipe_ingredients = [
                RecipeToIngredient(
                    recipe=recipe,
                    ingredient_id=ingredient['id'],
                    amount=ingredient['amount']
                ) for ingredient in ingredients_data
            ]
            RecipeToIngredient.objects.bulk_create(recipe_ingredients)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            RecipeToIngredient.objects.filter(recipe=instance).delete()

            recipe_ingredients = [
                RecipeToIngredient(
                    recipe=instance,
                    ingredient_id=ingredient['id'],
                    amount=ingredient['amount']
                ) for ingredient in ingredients_data
            ]
            RecipeToIngredient.objects.bulk_create(recipe_ingredients)

        return instance


class UserRecipeReadSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField()

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscribe.objects.filter(user=user, author=obj).exists()


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserRecipeReadSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    tags = TagSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_ingredients(self, obj):
        ingredients = obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('ingredient_list__amount'),
        )
        return ingredients

    def get_is_favorited(self, obj):
        request = self.context.get('request', None)
        user = request.user if request else None
        if user and user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request', None)
        user = request.user if request else None
        if user and user.is_authenticated:
            return ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        return False


class RecipeShortReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):

    name = serializers.CharField(source='recipe.name')
    image = Base64ImageField(source='recipe.image')
    cooking_time = serializers.IntegerField(source='recipe.cooking_time')

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartSerializer(serializers.ModelSerializer):

    name = serializers.CharField(source='recipe.name')
    image = Base64ImageField(source='recipe.image')
    cooking_time = serializers.IntegerField(source='recipe.cooking_time')

    class Meta:
        model = ShoppingCart
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class SubscribeSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    email = serializers.EmailField(source='author.email', read_only=True)
    id = serializers.IntegerField(source='author.id', read_only=True)
    username = serializers.CharField(source='author.username', read_only=True)
    first_name = serializers.CharField(
        source='author.first_name', read_only=True)
    last_name = serializers.CharField(
        source='author.last_name', read_only=True)
    avatar = Base64ImageField(source='author.avatar', read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscribe
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('current_user')
        return Subscribe.objects.filter(
            user=user, author=obj
        ).exists() if user and user.is_authenticated else False

    def get_recipes(self, obj):
        recipes = get_recipes_for_serializer(self, obj)
        return RecipeShortReadSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()
