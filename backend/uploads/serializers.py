from rest_framework import serializers
from .models import UploadedFile


class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ["id", "file", "filename", "file_size", "mime_type", "file_type", "created_at"]
        read_only_fields = ["id", "file_size", "mime_type", "file_type", "created_at"]
