from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'email', 'is_staff', 'is_superuser', 'is_active')

    list_filter = ('is_staff', 'is_superuser', 'is_active')

    search_fields = ('username', 'email')

    ordering = ('id',)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)