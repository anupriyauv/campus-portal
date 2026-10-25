from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'get_full_name', 'role', 'department', 'is_active', 'avatar_preview']
    list_filter = ['role', 'is_active', 'is_staff', 'department', 'semester']
    search_fields = ['email', 'username', 'first_name', 'last_name', 'usn']
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Authentication', {
            'fields': ('email', 'username', 'password')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'usn', 'department', 'semester', 'phone', 'bio', 'avatar')
        }),
        ('Role & Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['last_login', 'date_joined']
    
    @admin.display(description='Avatar')
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.avatar.url)
        return '-'
    
    actions = ['make_coordinator', 'make_student', 'activate_users', 'deactivate_users']
    
    @admin.action(description='Mark selected users as Coordinators')
    def make_coordinator(self, request, queryset):
        updated = queryset.update(role='COORDINATOR')
        self.message_user(request, f'{updated} users were successfully marked as coordinators.')
    
    @admin.action(description='Mark selected users as Students')
    def make_student(self, request, queryset):
        updated = queryset.update(role='STUDENT')
        self.message_user(request, f'{updated} users were successfully marked as students.')
    
    @admin.action(description='Activate selected users')
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users were successfully activated.')
    
    @admin.action(description='Deactivate selected users')
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users were successfully deactivated.')