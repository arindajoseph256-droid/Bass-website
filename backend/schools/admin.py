from django.contrib import admin
from .models import School, SchoolMembership


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ["name", "admin", "is_active", "total_teachers", "total_students", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "admin__email"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(SchoolMembership)
class SchoolMembershipAdmin(admin.ModelAdmin):
    list_display = ["school", "user", "role", "is_active", "joined_at"]
    list_filter = ["role", "is_active", "joined_at"]
    search_fields = ["school__name", "user__email"]
