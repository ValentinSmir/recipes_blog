import base64

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from rest_framework import serializers

from recipes.models import (Recipe, Ingredient, Tag, IngredientRecipe)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                if len(imgstr) > 100000:
                    raise ValidationError("Изображение слишком большое")
                return ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}'
                                   )
            except Exception as e:
                raise ValidationError(str(e))
        return super().to_internal_value(data)


class MyUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.subscriptions.filter(author=obj).exists()
        return False


class MyUserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'password')
        extra_kwargs = {
            'password': {'write_only': True}
        }


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = MyUserSerializer()
    ingredients = IngredientRecipeSerializer(
        many=True, source='infredients_recipe'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'description', 'cooking_time',
                  'created_at')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorites_r.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.shopping_cart.filter(user=request.user).exists()
        return False


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = serializers.JSONField(required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=True
    )
    image = Base64ImageField(required=True)
    text = serializers.CharField(source='description', required=True,
                                 write_only=True)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image', 'name',
                  'text', 'cooking_time')
        extra_kwargs = {
            'name': {'max_length': 256},
            'cooking_time': {'min_value': 1}
        }

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один ингредиент'
            )
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один тег'
            )
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        validated_data.pop('author', None)
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data)
        recipe.tags.set(tags)
        ingredient_objs = []
        for ingredient in ingredients:
            try:
                ingredient_obj = Ingredient.objects.get(id=ingredient['id'])
                ingredient_objs.append(
                    IngredientRecipe(
                        recipe=recipe,
                        ingredient=ingredient_obj,
                        amount=ingredient['amount']
                    )
                )
            except Ingredient.DoesNotExist:
                raise serializers.ValidationError(
                    {'ingredients': (
                        f'Ингредиент с id {ingredient["id"]} не найден')}
                )
        IngredientRecipe.objects.bulk_create(ingredient_objs)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)

        if ingredients is not None:
            instance.infredients_recipe.all().delete()

        ingredient_objs = []
        for ingredient in ingredients:
            try:
                ingredient_obj = Ingredient.objects.get(id=ingredient['id'])
                ingredient_objs.append(
                    IngredientRecipe(
                        recipe=instance,
                        ingredient=ingredient_obj,
                        amount=ingredient['amount']
                    )
                )
            except Ingredient.DoesNotExist:
                raise serializers.ValidationError(
                    {'ingredients': (
                        f'Ингредиент с id {ingredient["id"]} не найден')}
                )
        IngredientRecipe.objects.bulk_create(ingredient_objs)
        return instance

    def to_representation(self, instance):
        return RecipeListSerializer(
            instance,
            context=self.context
        ).data
