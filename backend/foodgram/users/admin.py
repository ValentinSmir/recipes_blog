
from django.contrib import admin

from .models import MyUser


class MyUserAdmin(admin.ModelAdmin):
    search_fields = ('email', 'username', 'first_name',)


admin.site.register(MyUser, MyUserAdmin)
