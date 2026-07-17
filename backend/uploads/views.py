from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import mimetypes

from common.paginations import StandardResultsSetPagination
from .models import UploadedFile
from .serializers import UploadedFileSerializer


class UploadViewSet(viewsets.ModelViewSet):
    """ViewSet for file uploads."""

    serializer_class = UploadedFileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return UploadedFile.objects.filter(uploaded_by=self.request.user)

    def create(self, request, *args, **kwargs):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        mime_type = file.content_type or mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        
        # Determine file type
        if mime_type.startswith("image"):
            file_type = UploadedFile.Type.IMAGE
        elif mime_type.startswith("video"):
            file_type = UploadedFile.Type.VIDEO
        elif mime_type.startswith("audio"):
            file_type = UploadedFile.Type.AUDIO
        elif mime_type in ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            file_type = UploadedFile.Type.DOCUMENT
        else:
            file_type = UploadedFile.Type.OTHER
        
        uploaded_file = UploadedFile.objects.create(
            uploaded_by=request.user,
            file=file,
            filename=file.name,
            file_size=file.size,
            mime_type=mime_type,
            file_type=file_type,
        )
        
        return Response(
            UploadedFileSerializer(uploaded_file).data,
            status=status.HTTP_201_CREATED,
        )
