
from django.contrib import admin

from .models import User


class MyUserAdmin(admin.ModelAdmin):
    search_fields = ('email', 'username', 'first_name',)


admin.site.register(User, MyUserAdmin)
