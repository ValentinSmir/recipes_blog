
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import MyUser


class MyUserAdmin(admin.ModelAdmin):
    search_fields = ('email', 'username', 'first_name',)


admin.site.register(MyUser, MyUserAdmin)
