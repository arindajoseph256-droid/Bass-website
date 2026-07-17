from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """Allows access only to admin users."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsTeacherUser(permissions.BasePermission):
    """Allows access only to teacher users."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_teacher


class IsStudentUser(permissions.BasePermission):
    """Allows access only to student users."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_student


class IsSchoolAdminUser(permissions.BasePermission):
    """Allows access only to school admin users."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_school_admin


class IsModeratorUser(permissions.BasePermission):
    """Allows access only to moderator users."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_moderator


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allows read access to everyone, but write access only to owners."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user or request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """Allows access only to owners or admin users."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        if hasattr(obj, "user"):
            return obj.user == request.user
        return obj == request.user


class IsTeacherOrAdmin(permissions.BasePermission):
    """Allows access to teachers and admin users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_teacher or request.user.is_admin or request.user.is_school_admin)
        )


class IsEnrolledStudentOrTeacher(permissions.BasePermission):
    """Allows access to enrolled students, teachers, or admin users."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_admin or request.user.is_teacher or request.user.is_school_admin:
            return True
        return request.user.is_student

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin or request.user.is_teacher or request.user.is_school_admin:
            return True
        if hasattr(obj, "students"):
            return request.user in obj.students.all()
        if hasattr(obj, "enrolled_students"):
            return request.user in obj.enrolled_students.all()
        return True


class ReadOnly(permissions.BasePermission):
    """Allows read-only access."""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
