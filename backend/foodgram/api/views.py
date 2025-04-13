from hashlib import md5

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import filters, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated, AllowAny,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import (Recipe, Ingredient, Tag, Favorite,
                            ShoppingCart, IngredientRecipe)
from .serializers import (MyUserSerializer,
                          TagSerializer,
                          RecipeCreateUpdateSerializer,
                          RecipeListSerializer,
                          IngredientSerializer,
                          SubscriptionSerializer)


User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    @action(
        methods=['put', 'delete'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def set_delete_avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {'error': 'Обязательное поле.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user.avatar = request.data['avatar']
                user.save()
                return Response(
                    {'avatar': user.avatar.url},
                    status=status.HTTP_200_OK
                )
            except ValidationError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        elif request.method == 'DELETE':
            if default_storage.exists(user.avatar.name):
                default_storage.delete(user.avatar.name)
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        subscribed_users = User.objects.filter(
            subscribers__user=user).prefetch_related('recipes')

        serializer = SubscriptionSerializer(
            subscribed_users,
            many=True,
            context={'request': request}
        )

        # data = serializer.data
        # for author_data, author in zip(data, subscribed_users):
        #     recipes = author.recipes.all()
        #     author_data['recipes'] = [
        #         {
        #             'id': recipe.id,
        #             'name': recipe.name,
        #             'image': recipe.image.url if recipe.image else None,
        #             'cooking_time': recipe.cooking_time
        #         }
        #         for recipe in recipes
        #     ]
        #     author_data['recipes_count'] = len(author_data['recipes'])

        return Response(serializer.data)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            serializer = SubscriptionSerializer(author,
                                                data=request.data,
                                                context={'request': request})
            serializer.is_valid(raise_exception=True)
            # if user == author:
            #     return Response(
            #         {'error': 'Нельзя подписаться на самого себя.'},
            #         status=status.HTTP_400_BAD_REQUEST
            #     )
            # if user.subscriptions.filter(author=author).exists():
            #     return Response(
            #         {'error': 'Вы уже подписаны на этого пользователя.'},
            #         status=status.HTTP_400_BAD_REQUEST
            #     )
            user.subscriptions.create(author=author)
            # recipes = author.recipes.all()
            # response_data['recipes'] = [
            #     {
            #         'id': recipe.id,
            #         'name': recipe.name,
            #         'image': recipe.image.url,
            #         'cooking_time': recipe.cooking_time
            #     }
            #     for recipe in recipes]
            # response_data['recipes_count'] = author.recipes.count()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            subscription = user.subscriptions.get(author=author)
            # subscription = user.subscriptions.filter(author=author).first()
            if not subscription:
                return Response(
                    {'error': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'id'
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['tags__slug', 'author']
    search_fields = ['name']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeListSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'get_short_link']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited == '1' and user.is_authenticated:
            queryset = queryset.filter(favorites_r__user=user)

        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        if is_in_shopping_cart == '1' and user.is_authenticated:
            queryset = queryset.filter(shopping_cart__user=user)

        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        return queryset.select_related('author').prefetch_related(
            'tags', 'infredients_recipe__ingredient'
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return Response(
                {'detail': 'Недостаточно прав для выполнения операции.'},
                status=status.HTTP_403_FORBIDDEN
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if user.favorites.filter(recipe=recipe).exists():
            # if Favorite.objects.filter(user=request.user,
            #                            recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=request.user, recipe=recipe)
            return Response(
                {'id': recipe.id, 'name': recipe.name,
                 'image': recipe.image.url,
                 'cooking_time': recipe.cooking_time},
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            favorite, _ = user.favorites.filter(recipe=recipe).delete()
            # favorite = Favorite.objects.filter(user=request.user,
            #                                    recipe=recipe)
            if favorite == 0:
                return Response(
                    {'errors': 'Рецепта нет в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if user.shopping_cart_user.filter(recipe=recipe).exists():
            # if ShoppingCart.objects.filter(user=request.user,
            #                                recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            return Response(
                {'id': recipe.id, 'name': recipe.name,
                 'image': recipe.image.url,
                 'cooking_time': recipe.cooking_time},
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            cart, _ = user.shopping_cart_user.filter(recipe=recipe).delete()
            if cart == 0:
                return Response(
                    {'errors': 'Рецепта нет в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        # shopping_cart = ShoppingCart.objects.filter(user=request.user)
        # recipes = [item.recipe for item in shopping_cart]
        # recipes = request.user.shopping_cart_user.all().select_related(
        #     'recipe')
        # ingredients = {}
        # for recipe in recipes:
        #     for ingredient_recipe in recipe.infredients_recipe.all():
        #         name = ingredient_recipe.ingredient.name
        #         amount = ingredient_recipe.amount
        #         measurement_unit = (ingredient_recipe.ingredient
        #                             .measurement_unit)
        #         if name in ingredients:
        #             ingredients[name]['amount'] += amount
        #         else:
        #             ingredients[name] = {
        #                 'amount': amount,
        #                 'measurement_unit': measurement_unit
        #             }
        ingredients_data = (
            IngredientRecipe.objects
            .filter(recipe__shopping_cart__user=request.user)
            .values(
                'ingredient__name',
                'ingredient__measurement_unit'
            )
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )
        file_content = ['Список покупок:\n']
        for index, item in enumerate(ingredients_data, start=1):
            file_content.append(f"{index}. {item['ingredient__name']} - "
                                f"{item['total_amount']} "
                                f"{item['ingredient__measurement_unit']}\n")
        response = HttpResponse(''.join(file_content),
                                content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = ('attachment;'
                                           'filename="shopping_list.txt"')
        return response

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[AllowAny],
        url_path='get-link',
        url_name='get_short_link'
    )
    def get_short_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = self._generate_short_link(recipe)
        return Response(
            {'short-link': short_link},
            status=status.HTTP_200_OK
        )

    def _generate_short_link(self, recipe):
        hash_str = md5(str(recipe.id).encode()).hexdigest()[:6]
        return f'{settings.FOODGRAM_BASE_URL}/r/{hash_str}'


class ShortLinkRedirectView(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    lookup_field = 'hash_str'

    def retrieve(self, request, hash_str=None):
        recipes = Recipe.objects.all()
        for recipe in recipes:
            if md5(str(recipe.id).encode()).hexdigest()[:6] == hash_str:
                return redirect('recipe-detail', pk=recipe.pk)
        return Response(
            {'error': 'Рецепт не найден'},
            status=status.HTTP_404_NOT_FOUND
        )
