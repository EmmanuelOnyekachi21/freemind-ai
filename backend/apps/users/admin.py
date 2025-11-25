from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.users.models import Account

# Register your models here.
@admin.register(Account)
class AccountAdmin(UserAdmin):
    list_display = [
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_superuser',
        'is_active'
    ]
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {"fields": ('email', 'password')}),
        ('Personal Information', {'fields': ('first_name', 'last_name', 'phone_number', 'date_of_birth', 'gender')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)