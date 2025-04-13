from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

MAX_LENGHT_NAME_INGREDIENT = 128
MAX_LENGHT_MEASUREMENT_UNIT = 64
MAX_LENGHT_TAG = 32
MAX_LENGHT_RECIPE = 256
MAX_LENGHT_SHORTLINK = 10
MAX_LENGHT = 32000
MIN_LENGHT = 1


class Ingredient(models.Model):
    name = models.CharField(max_length=MAX_LENGHT_NAME_INGREDIENT,
                            verbose_name='Название ингредиента')
    measurement_unit = models.CharField(max_length=MAX_LENGHT_MEASUREMENT_UNIT,
                                        verbose_name='Единица измерения')

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} {self.measurement_unit}'


class Tag(models.Model):
    name = models.CharField(max_length=MAX_LENGHT_TAG, unique=True,
                            verbose_name='Название тега')
    slug = models.SlugField(max_length=MAX_LENGHT_TAG, unique=True,
                            verbose_name='слаг')

    class Meta:
        ordering = ['id']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(User, related_name='recipes',
                               on_delete=models.CASCADE,
                               verbose_name='Автор')
    name = models.CharField(max_length=MAX_LENGHT_RECIPE,
                            verbose_name='Название рецепта')
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Картинка'
    )
    description = models.TextField(verbose_name='Описание рецепта')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='IngredientRecipe',
                                         verbose_name='Ингредиенты')
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                1,
                message='Время приготовления должно быть не менее 1 минуты'),
            MaxValueValidator(
                32000,
                message='Время приготовления не должно превышать 32,000 минут')
        ],
        verbose_name='Время приготовления')
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='favorites',
                             verbose_name='Пользователь')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='favorites_r',
                               verbose_name='Рецепт')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]
        ordering = ['recipe']
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='subscriptions',
                             verbose_name='Пользователь')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='subscribers',
                               verbose_name='Автор')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]
        ordering = ['author']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} - {self.author}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart_user',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт',
    )

    class Meta:
        ordering = ['recipe']
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзина покупок'
        constraints = [models.UniqueConstraint(fields=['user', 'recipe'],
                                               name='unique_shopping_cart')]

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в Корзину покупок'


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   related_name='infredients_recipe',
                                   verbose_name='Ингредиент')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='infredients_recipe',
                               verbose_name='Рецепт')
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(
                1,
                message='Время приготовления должно быть не менее 1 минуты'),
            MaxValueValidator(
                32000,
                message='Время приготовления не должно превышать 32,000 минут')
        ])

    class Meta:
        ordering = ['ingredient']

    def __str__(self):
        return (f'{self.ingredient.name} - '
                f'{self.amount} {self.ingredient.measurement_unit}')


class TagRecipe(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE,
                            related_name='recipe_tag',
                            verbose_name='Тег')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='recipe_tag',
                               verbose_name='Рецепт',
                               )

    class Meta:
        ordering = ['tag']


class ShortLink(models.Model):
    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        related_name='short_link'
    )
    hash = models.CharField(max_length=MAX_LENGHT_SHORTLINK, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
