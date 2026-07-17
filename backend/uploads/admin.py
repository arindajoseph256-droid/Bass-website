from django.contrib import admin
from .models import UploadedFile


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ["filename", "uploaded_by", "file_type", "file_size", "created_at"]
    list_filter = ["file_type", "created_at"]
    search_fields = ["filename", "uploaded_by__email"]
