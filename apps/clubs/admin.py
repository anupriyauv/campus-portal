from django.contrib import admin
from .models import Club, ClubMembership

class ClubMembershipInline(admin.TabularInline):
    model = ClubMembership
    extra = 0
    raw_id_fields = ['user']

@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'coordinator', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description', 'coordinator__username')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ClubMembershipInline]
    raw_id_fields = ['coordinator']
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(ClubMembership)
class ClubMembershipAdmin(admin.ModelAdmin):
    list_display = ('club', 'user', 'role', 'joined_date', 'is_active')
    list_filter = ('role', 'is_active', 'club')
    search_fields = ('club__name', 'user__username')
    date_hierarchy = 'joined_date'
    raw_id_fields = ['club', 'user']