from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from common.permissions import IsSchoolAdminUser, IsAdminUser
from common.paginations import StandardResultsSetPagination
from .models import School, SchoolMembership
from .serializers import SchoolSerializer, SchoolMembershipSerializer


class SchoolViewSet(viewsets.ModelViewSet):
    """ViewSet for schools."""

    queryset = School.objects.filter(is_active=True)
    serializer_class = SchoolSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return super().get_permissions()


class SchoolMembershipViewSet(viewsets.ModelViewSet):
    """ViewSet for school memberships."""

    serializer_class = SchoolMembershipSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_school_admin:
            school_id = self.kwargs.get("school_id")
            if school_id:
                return SchoolMembership.objects.filter(school_id=school_id)
            return SchoolMembership.objects.filter(school__admin=user)
        return SchoolMembership.objects.filter(user=user)
