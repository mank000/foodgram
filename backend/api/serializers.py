import base64
import re

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import F
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from foodgram.const import MAX_LENGTH_EMAIL, MAX_LENGTH_SERIALIZERS
from users.models import Favorite, ShoppingCart, Subscribe

from .models import Ingredient, Recipe, RecipeToIngredient, Tag

User = get_user_model()


class UserCreateSerializer(UserCreateSerializer):
    """Кастомные поля для регистарции."""

    email = serializers.EmailField(
        required=True,
        max_length=MAX_LENGTH_EMAIL,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Пользователь с таким email уже существует.",
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
        style={"input_type": "password"},
        write_only=True,
    )

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
        )

    def validate_username(self, value):
        """Валидация имени пользователя."""
        if not re.match(r"^[\w.@+-]+$", value):
            raise serializers.ValidationError("Выберите другой ник")
        return value


class UserProfileSerializer(UserCreateSerializer):
    """Сериализатор профиля пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Subscribe.objects.filter(user=user, author=obj).exists()

    def to_representation(self, instance):

        if isinstance(instance, User) and instance.is_anonymous:
            representation = super().to_representation(instance)
            representation.pop("email", None)
            return representation
        return super().to_representation(instance)


class UserProfileSerializerWithRecipes(serializers.ModelSerializer):

    recipes = serializers.SerializerMethodField()

    recipes_count = serializers.SerializerMethodField()

    is_subscribed = serializers.SerializerMethodField()

    class Meta:

        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = request.query_params.get("recipes_limit")
        recipes = Recipe.objects.filter(author=obj)
        if limit:
            recipes = recipes[: int(limit)]
        return RecipeShortReadSerializer(
            recipes, many=True, context=self.context
        ).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    def get_is_subscribed(self, obj):
        return True


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):

        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)
        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(
        required=True,
    )

    class Meta:
        model = User
        fields = [
            "avatar",
        ]


class UserListProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "avatar",
        )


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


# Дописать


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField()

    class Meta:
        model = RecipeToIngredient
        fields = (
            "id",
            "amount",
        )


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField(required=True, allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time",
        )

    def validate_ingredients(self, value):
        if "ingredients" not in self.initial_data:
            raise ValidationError(
                {"ingredients": "Нужен хотя бы один ингредиент!"}
            )
        if len(value) == 0:
            raise ValidationError("Нужен хотя бы один ингредиент!")
        ingrediens_list = []
        for val in value:
            try:
                ingredient = Ingredient.objects.get(id=val["id"])
            except Ingredient.DoesNotExist:
                raise serializers.ValidationError("Ингредиент не найден!")
            if ingredient in ingrediens_list:
                raise ValidationError("Ингредиент не должны повторятся!")
            ingrediens_list.append(ingredient)
            if val["amount"] <= 0:
                raise ValidationError(
                    "Количество ингредиента должно быть больше 0!"
                )
        return value

    def validate_tags(self, value):
        if len(value) == 0:
            raise ValidationError("Нужен хотя бы один тег!")
        tag_list = []
        for val in value:
            if val in tag_list:
                raise ValidationError("Тег не должен повторятся!")
            tag_list.append(val)
        return value

    def to_representation(self, instance):
        return RecipeReadSerializer(instance).data


class RecipeReadSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    tags = TagSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def get_author(self, obj):
        print(obj.author)
        return UserRecipeReadSerializer(obj.author).data

    def get_ingredients(self, obj):
        ingredients = obj.ingredients.values(
            "id",
            "name",
            "measurement_unit",
            amount=F("ingredientlist__amount"),
        )
        return ingredients

    def get_is_favorited(self, instance):
        #

        return True

    def get_is_in_shopping_cart(self, instance):
        #

        return True


class RecipeShortReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class UserRecipeReadSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField()

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        return False


class FavoriteSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField()

    image = serializers.SerializerMethodField()

    cooking_time = serializers.SerializerMethodField()

    class Meta:
        model = Favorite
        fields = ("id", "name", "image", "cooking_time")

    def get_name(self, obj):
        return obj.recipe.name

    def get_image(self, obj):
        return obj.recipe.image.url

    def get_cooking_time(self, obj):
        return obj.recipe.cooking_time


class ShoppingCartSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField()

    image = serializers.SerializerMethodField()

    cooking_time = serializers.SerializerMethodField()

    class Meta:
        model = ShoppingCart
        fields = (
            "id",
            "name",
            "image",
            "cooking_time",
        )

    def get_name(self, obj):
        return obj.recipe.name

    def get_image(self, obj):
        return obj.recipe.image.url

    def get_cooking_time(self, obj):
        return obj.recipe.cooking_time


class SubscibeSerializer(serializers.ModelSerializer):

    recipes = serializers.SerializerMethodField()

    class Meta:
        model = Subscribe
        fields = ("recipes",)

    def to_representation(self, instance):

        if isinstance(instance, User) and not instance.is_anonymous:
            representation = super().to_representation(instance)
            representation["email"] = instance.email
            representation["id"] = instance.id
            representation["username"] = instance.username
            representation["first_name"] = instance.first_name
            representation["last_name"] = instance.last_name
            representation["is_subscribed"] = True
            representation["recipes_count"] = (
                Recipe.objects.all().filter(author=instance).count()
            )

            if instance.avatar:
                representation["avatar"] = instance.avatar.url
            else:
                representation["avatar"] = None
            return representation
        return super().to_representation(instance)

    def get_recipes(self, obj):

        recipes = Recipe.objects.filter(author=obj)

        recipes_limit = self.context.get("recipes_limit")

        if recipes_limit is not None:
            recipes = recipes[:recipes_limit]
        return RecipeShortReadSerializer(recipes, many=True).data
