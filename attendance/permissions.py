"""
Role-based authorization utilities and decorators (Issue #12).

Traceability:
- Functional Requirement: REQ-02 (Provide role-based access)
- Business Rules:
    - BR-01: Only authenticated users shall access protected system functions.
    - BR-02: Administrators shall manage system-level student, faculty, and course/class information.
    - BR-03: Faculty members shall mark attendance only for their assigned classes.
    - BR-04: Students shall be allowed to view only their own attendance records.
    - BR-05: Faculty members shall be allowed to modify attendance records only for classes assigned to them.
- Test Plan v1.1 cases: UT-02-01, UT-02-02, UT-02-03, IT-02-01, IT-02-02, ST-02-01
"""

from functools import wraps
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def role_required(*allowed_roles):
    """
    Decorator for views that enforces server-side role-based access control:
    - If the user is unauthenticated: redirect to LOGIN_URL with ?next= (HTTP 302).
    - If the user is authenticated but not in allowed_roles: raise PermissionDenied (HTTP 403 Forbidden).
    - If the user has a permitted role: execute the view.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(
                    request.get_full_path(),
                    login_url=settings.LOGIN_URL,
                )
            if getattr(request.user, "role", None) not in allowed_roles:
                raise PermissionDenied(
                    "You do not have permission to access this resource."
                )
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """Decorator ensuring the view can only be accessed by authenticated Administrators."""
    return role_required("ADMIN")(view_func)


def faculty_required(view_func):
    """Decorator ensuring the view can only be accessed by authenticated Faculty or Administrators."""
    return role_required("FACULTY", "ADMIN")(view_func)


def student_required(view_func):
    """Decorator ensuring the view can only be accessed by authenticated Students or Administrators."""
    return role_required("STUDENT", "ADMIN")(view_func)


def can_manage_courses(user):
    """Check if the user is an authenticated administrator authorized to manage courses."""
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and getattr(user, "role", None) == "ADMIN"
    )


def can_faculty_manage_section(user, class_section):
    """Check if user is an administrator or the faculty assigned to this class section."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    user_role = getattr(user, "role", None)
    if user_role == "ADMIN":
        return True
    if user_role == "FACULTY":
        faculty_user_id = getattr(class_section.faculty, "user_id", None)
        return bool(faculty_user_id and faculty_user_id == getattr(user, "pk", None))
    return False


def can_student_view_attendance(user, student):
    """Check if user is an administrator, assigned faculty, or the student viewing own record."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    user_role = getattr(user, "role", None)
    if user_role == "ADMIN":
        return True
    if user_role == "STUDENT":
        student_user_id = getattr(student, "user_id", None)
        return bool(student_user_id and student_user_id == getattr(user, "pk", None))
    if user_role == "FACULTY":
        user_pk = getattr(user, "pk", None)
        if not user_pk:
            return False
        return student.enrollments.filter(
            class_section__faculty__user_id=user_pk
        ).exists()
    return False
