from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from common.permissions import IsAdminUser
from common.paginations import StandardResultsSetPagination
from accounts.models import User, UserSession
from accounts.serializers import UserSerializer
from .serializers import UserSessionSerializer


class UserManagementViewSet(viewsets.ModelViewSet):
    """ViewSet for user management (admin only)."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filterset_fields = ["role", "is_verified", "is_active"]
    search_fields = ["email", "first_name", "last_name", "username"]

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        user = self.get_object()
        user.is_verified = True
        user.save(update_fields=["is_verified"])
        return Response({"success": True, "message": "User verified."})

    @action(detail=True, methods=["post"])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        return Response({"success": True, "is_active": user.is_active})

    @action(detail=True, methods=["get"])
    def sessions(self, request, pk=None):
        user = self.get_object()
        sessions = UserSession.objects.filter(user=user, is_active=True)
        return Response({
            "sessions": UserSessionSerializer(sessions, many=True).data,
        })

    @action(detail=True, methods=["post"])
    def logout_all(self, request, pk=None):
        user = self.get_object()
        UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
        return Response({"success": True, "message": "All sessions terminated."})
