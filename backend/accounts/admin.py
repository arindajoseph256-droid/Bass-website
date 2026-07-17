from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        "email", "first_name", "last_name", "role",
        "is_verified", "is_active", "is_staff", "points", "date_joined",
    ]
    list_filter = ["role", "is_verified", "is_active", "is_staff", "date_joined"]
    search_fields = ["email", "first_name", "last_name", "username"]
    ordering = ["-date_joined"]
    
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "gender", "phone", "bio", "date_of_birth", "profile_image", "cover_image")}),
        ("Location", {"fields": ("address", "city", "country", "postal_code")}),
        ("Role & Permissions", {"fields": ("role", "is_verified", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Social", {"fields": ("website", "linkedin", "twitter", "github")}),
        ("Preferences", {"fields": ("email_notifications", "push_notifications", "language", "timezone", "dark_mode")}),
        ("Gamification", {"fields": ("badges", "points")}),
        ("Privacy", {"fields": ("is_public", "show_email", "show_profile")}),
        ("Activity", {"fields": ("last_login", "last_activity", "last_login_ip")}),
        ("Dates", {"fields": ("date_joined",)}),
    )
    
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "first_name", "last_name", "role"),
        }),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ["user", "ip_address", "created_at", "expires_at", "is_active"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["user__email", "ip_address"]
    ordering = ["-created_at"]
