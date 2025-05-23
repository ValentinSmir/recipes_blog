from django.contrib import admin

from .models import (Ingredient, Tag, Recipe, Favorite,
                     Subscription, IngredientRecipe,
                     TagRecipe)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author',)
    search_fields = ('name', 'author',)
    list_filter = ('tags',)
    filter_horizontal = ('tags',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    search_fields = ('name',)


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Favorite)
admin.site.register(Subscription)
admin.site.register(IngredientRecipe)
admin.site.register(TagRecipe)
admin.site.empty_value_display = 'Не задано'
