import time

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import (
    Student,
    Faculty,
    Course,
    ClassSection,
    Enrollment,
    AttendanceSession,
    AttendanceRecord,
    AttendanceAudit,
)
from .services import mark_attendance, update_attendance


User = get_user_model()


class AttendanceServiceTests(TestCase):
    def setUp(self):
        self.faculty_user = User.objects.create_user(
            username="faculty1",
            password="test-password-123",
            role=User.Role.FACULTY,
        )
        self.student_user = User.objects.create_user(
            username="student1",
            password="test-password-123",
            role=User.Role.STUDENT,
        )

        self.student = Student.objects.create(
            usn="TEST001",
            user=self.student_user,
            name="Test Student",
            email="student@example.com",
            program="CSE",
            semester=3,
        )

        self.faculty = Faculty.objects.create(
            faculty_code="FAC001",
            user=self.faculty_user,
            name="Test Faculty",
            email="faculty@example.com",
            department="CSE",
        )

        self.course = Course.objects.create(
            course_code="CS101",
            course_name="Test Course",
            semester=3,
        )

        self.section = ClassSection.objects.create(
            course=self.course,
            faculty=self.faculty,
            section="A",
            academic_term="2026-27",
        )

        self.session = AttendanceSession.objects.create(
            class_section=self.section,
            session_date="2026-10-22",
            session_no=1,
        )

        Enrollment.objects.create(
            student=self.student,
            class_section=self.section,
        )

    def test_mark_attendance_for_enrolled_student(self):
        record = mark_attendance(
            session_id=self.session.pk,
            student_id=self.student.pk,
            status=AttendanceRecord.Status.PRESENT,
            marked_by=self.faculty_user,
        )

        self.assertEqual(
            record.status,
            AttendanceRecord.Status.PRESENT,
        )
        self.assertEqual(record.marked_by, self.faculty_user)
        self.assertEqual(AttendanceRecord.objects.count(), 1)

    def test_reject_attendance_for_unenrolled_student(self):
        other = Student.objects.create(
            usn="TEST002",
            name="Other Student",
            email="other@example.com",
            program="CSE",
            semester=3,
        )

        with self.assertRaises(ValidationError):
            mark_attendance(
                session_id=self.session.pk,
                student_id=other.pk,
                status=AttendanceRecord.Status.PRESENT,
                marked_by=self.faculty_user,
            )

        self.assertEqual(AttendanceRecord.objects.count(), 0)

    def test_reject_invalid_status(self):
        with self.assertRaises(ValidationError):
            mark_attendance(
                session_id=self.session.pk,
                student_id=self.student.pk,
                status="LATE",
                marked_by=self.faculty_user,
            )

        self.assertEqual(AttendanceRecord.objects.count(), 0)

    def test_update_attendance_creates_audit_record(self):
        record = AttendanceRecord.objects.create(
            session=self.session,
            student=self.student,
            status=AttendanceRecord.Status.PRESENT,
            marked_by=self.faculty_user,
        )

        updated = update_attendance(
            attendance_id=record.pk,
            status=AttendanceRecord.Status.ABSENT,
            changed_by=self.faculty_user,
        )

        self.assertEqual(
            updated.status,
            AttendanceRecord.Status.ABSENT,
        )
        self.assertIsNotNone(updated.modified_at)
        self.assertEqual(AttendanceAudit.objects.count(), 1)

        audit = AttendanceAudit.objects.get()
        self.assertEqual(
            audit.old_status,
            AttendanceRecord.Status.PRESENT,
        )
        self.assertEqual(
            audit.new_status,
            AttendanceRecord.Status.ABSENT,
        )
        self.assertEqual(audit.changed_by, self.faculty_user)

    def test_duplicate_attendance_is_rejected(self):
        AttendanceRecord.objects.create(
            session=self.session,
            student=self.student,
            status=AttendanceRecord.Status.PRESENT,
            marked_by=self.faculty_user,
        )

        # The unique constraint must reject a second record for this
        # student and session. The nested transaction keeps the test usable.
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                mark_attendance(
                    session_id=self.session.pk,
                    student_id=self.student.pk,
                    status=AttendanceRecord.Status.ABSENT,
                    marked_by=self.faculty_user,
                )

        self.assertEqual(AttendanceRecord.objects.count(), 1)

    def test_unassigned_faculty_cannot_mark_attendance(self):
        other_user = User.objects.create_user(
            username="faculty2",
            password="test-password-123",
            role=User.Role.FACULTY,
        )

        with self.assertRaises(PermissionDenied):
            mark_attendance(
                session_id=self.session.pk,
                student_id=self.student.pk,
                status=AttendanceRecord.Status.PRESENT,
                marked_by=other_user,
            )

        self.assertEqual(AttendanceRecord.objects.count(), 0)

    def test_assigned_faculty_can_mark_attendance(self):
        record = mark_attendance(
            session_id=self.session.pk,
            student_id=self.student.pk,
            status=AttendanceRecord.Status.PRESENT,
            marked_by=self.faculty_user,
        )

        self.assertEqual(record.marked_by, self.faculty_user)
        self.assertEqual(AttendanceRecord.objects.count(), 1)

    def test_same_status_does_not_create_audit_record(self):
        record = AttendanceRecord.objects.create(
            session=self.session,
            student=self.student,
            status=AttendanceRecord.Status.PRESENT,
            marked_by=self.faculty_user,
        )

        updated = update_attendance(
            attendance_id=record.pk,
            status=AttendanceRecord.Status.PRESENT,
            changed_by=self.faculty_user,
        )

        self.assertEqual(
            updated.status,
            AttendanceRecord.Status.PRESENT,
        )
        self.assertEqual(AttendanceAudit.objects.count(), 0)


class AuthenticationTests(TestCase):
    """
    Tests for Issue #11: Login, logout, and session handling.
    Traceability:
    - Functional Requirement: REQ-01 (Authenticate registered users)
    - Business Rule: BR-01 (Only authenticated users access protected functions)
    - Test Plan v1.1 cases:
        - UT-01-01: Unit: Authenticate valid admin credentials
        - UT-01-02: Unit: Test login with an invalid password
        - UT-01-03: Unit: Test login with an unregistered username
        - UT-01-04: Unit: Test login with empty credential fields
        - IT-01-01: Integration: Verify database credential matching (hashed password)
        - ST-01-01: System: Verify login page performance (< 3s)
        - ST-02-01: System: Prevent unauthenticated access to protected features
        - ST-02-02: System: Verify session invalidation upon logout
    """

    def setUp(self):
        self.admin_password = "validAdminPass123"
        self.admin_user = User.objects.create_user(
            username="admin_01",
            password=self.admin_password,
            role=User.Role.ADMIN,
        )

        self.faculty_password = "validFacultyPass123"
        self.faculty_user = User.objects.create_user(
            username="faculty_01",
            password=self.faculty_password,
            role=User.Role.FACULTY,
        )

        self.student_password = "validStudentPass123"
        self.student_user = User.objects.create_user(
            username="student_01",
            password=self.student_password,
            role=User.Role.STUDENT,
        )

    def test_login_page_renders_successfully(self):
        """Verify GET /login/ returns 200, uses login template, and renders CSRF token."""
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, 'id="id_username"')
        self.assertContains(response, 'id="id_password"')

    def test_authenticate_valid_admin_credentials(self):
        """
        [UT-01-01 / AC-1] Unit: Authenticate valid admin credentials.
        Submit valid administrator credentials, verify successful authentication,
        redirection to home, and session establishment.
        """
        response = self.client.post(
            reverse("login"),
            {"username": "admin_01", "password": self.admin_password},
        )
        self.assertRedirects(response, reverse("home"))
        # Verify authenticated session exists
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.admin_user.pk)

    def test_authenticate_valid_faculty_credentials(self):
        """[AC-1] Verify registered faculty member can authenticate with valid credentials."""
        response = self.client.post(
            reverse("login"),
            {"username": "faculty_01", "password": self.faculty_password},
        )
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.faculty_user.pk)

    def test_login_with_invalid_password(self):
        """
        [UT-01-02 / AC-2] Unit: Test login with an invalid password.
        Submit valid username with incorrect password, verify rejection and error message.
        """
        response = self.client.post(
            reverse("login"),
            {"username": "faculty_01", "password": "wrongPassword!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")
        self.assertContains(response, "Please enter a correct username and password")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_with_unregistered_username(self):
        """
        [UT-01-03 / AC-2] Unit: Test login with an unregistered username.
        Submit unknown username, verify rejection and error message.
        """
        response = self.client.post(
            reverse("login"),
            {"username": "unknown_user", "password": "Pass123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")
        self.assertContains(response, "Please enter a correct username and password")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_with_empty_credential_fields(self):
        """
        [UT-01-04 / AC-2] Unit: Test login with empty credential fields.
        Submit blank username and password, verify form validation error messages.
        """
        response = self.client.post(
            reverse("login"),
            {"username": "", "password": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")
        self.assertContains(response, "This field is required")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_passwords_are_stored_as_secure_hashes(self):
        """
        [AC-3 / IT-01-01] Passwords must be stored as secure hashes, never in plain text.
        Verify database password field is hashed with PBKDF2/SHA-256 and validates correctly.
        """
        user = User.objects.get(username="admin_01")
        self.assertNotEqual(user.password, self.admin_password)
        self.assertTrue(
            user.password.startswith("pbkdf2_sha256$")
            or user.password.startswith("argon2")
            or user.password.startswith("bcrypt"),
            f"Expected secure hash prefix, got {user.password[:15]}",
        )
        self.assertTrue(user.check_password(self.admin_password))
        self.assertFalse(user.check_password("wrong_password"))

    def test_unauthenticated_access_to_protected_page_redirects_to_login(self):
        """
        [BR-01 / ST-02-01 / AC-4] Prevent unauthenticated access to protected features.
        Enforces Business Rule BR-01: unauthenticated requests to protected views
        must be redirected to the login interface.
        """
        response = self.client.get(reverse("home"))
        expected_redirect_url = f"{reverse('login')}?next={reverse('home')}"
        self.assertRedirects(response, expected_redirect_url)

    def test_authenticated_user_can_access_protected_page(self):
        """[BR-01 / AC-1 / AC-4] Authenticated user can access protected home landing page."""
        self.client.login(username="admin_01", password=self.admin_password)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")
        self.assertContains(response, "admin_01")
        self.assertContains(response, "Administrator")

    def test_logout_via_post_invalidates_session(self):
        """
        [ST-02-02 / AC-5 / Adjustment 1] Verify session invalidation upon logout.
        Submitting POST to /logout/ terminates session and redirects to login.
        Subsequent request to protected page is denied / redirected.
        """
        self.client.login(username="admin_01", password=self.admin_password)
        # Ensure authenticated
        home_res = self.client.get(reverse("home"))
        self.assertEqual(home_res.status_code, 200)

        # Logout via POST (Django 5.x CSRF-protected POST)
        logout_res = self.client.post(reverse("logout"))
        self.assertRedirects(logout_res, reverse("login"))

        # Verify session is invalidated
        self.assertNotIn("_auth_user_id", self.client.session)

        # Back navigation / re-accessing protected page must redirect to login (ST-02-02)
        protected_res = self.client.get(reverse("home"))
        self.assertRedirects(
            protected_res, f"{reverse('login')}?next={reverse('home')}"
        )

    def test_logout_via_get_is_disallowed(self):
        """
        [Adjustment 1] Logout must use POST with CSRF protection.
        GET request to logout must return 405 Method Not Allowed.
        """
        self.client.login(username="admin_01", password=self.admin_password)
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)

    def test_login_page_performance_within_3_seconds(self):
        """
        [ST-01-01 / AC-6 / Adjustment 3] Verify login page loads within 3 seconds
        under normal operating conditions.
        """
        start_time = time.perf_counter()
        response = self.client.get(reverse("login"))
        elapsed_seconds = time.perf_counter() - start_time

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            elapsed_seconds,
            3.0,
            f"Login page load took {elapsed_seconds:.4f}s, exceeding 3.0s threshold",
        )

    def test_login_with_inactive_user_is_rejected(self):
        """
        [AC-2 / REQ-01] Inactive accounts must be rejected during authentication.
        Verify that a user marked is_active=False cannot authenticate,
        receives the appropriate error message, and no session is created.
        """
        inactive_password = "inactivePassword123"
        User.objects.create_user(
            username="inactive_01",
            password=inactive_password,
            role=User.Role.STUDENT,
            is_active=False,
        )
        response = self.client.post(
            reverse("login"),
            {"username": "inactive_01", "password": inactive_password},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")
        self.assertContains(response, "Please enter a correct username and password")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_rotates_session_key(self):
        """
        [Security / NFR] Verify session key rotation upon login to prevent session fixation.
        The session key before authentication must differ from the session key after authentication.
        """
        # Obtain pre-login session key
        self.client.get(reverse("login"))
        pre_login_session_key = self.client.session.session_key

        # Authenticate
        response = self.client.post(
            reverse("login"),
            {"username": "admin_01", "password": self.admin_password},
        )
        self.assertRedirects(response, reverse("home"))

        post_login_session_key = self.client.session.session_key
        self.assertIsNotNone(post_login_session_key)
        self.assertNotEqual(
            pre_login_session_key,
            post_login_session_key,
            "Session key must cycle/rotate upon successful authentication",
        )
class StudentAttendanceHistoryTests(TestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(
            username="history_student",
            password="test-password-123",
            role=User.Role.STUDENT,
        )
        self.student = Student.objects.create(
            usn="HIST001",
            user=self.student_user,
            name="History Student",
            email="history@example.com",
            program="CSE",
            semester=3,
        )

        self.other_student = Student.objects.create(
            usn="HIST002",
            name="Other Student",
            email="other-history@example.com",
            program="CSE",
            semester=3,
        )

        self.faculty_user = User.objects.create_user(
            username="history_faculty",
            password="test-password-123",
            role=User.Role.FACULTY,
        )
        self.admin_user = User.objects.create_user(
            username="history_admin",
            password="test-password-123",
            role=User.Role.ADMIN,
        )

        self.faculty = Faculty.objects.create(
            faculty_code="HISTFAC",
            user=self.faculty_user,
            name="History Faculty",
            email="history-faculty@example.com",
            department="CSE",
        )
        self.course = Course.objects.create(
            course_code="HIST101",
            course_name="History Test Course",
            semester=3,
        )
        self.section = ClassSection.objects.create(
            course=self.course,
            faculty=self.faculty,
            section="A",
            academic_term="2026-27",
        )
        self.session = AttendanceSession.objects.create(
            class_section=self.section,
            session_date="2026-10-22",
            session_no=1,
        )

        Enrollment.objects.create(
            student=self.student,
            class_section=self.section,
        )
        Enrollment.objects.create(
            student=self.other_student,
            class_section=self.section,
        )

    def test_student_sees_only_own_history(self):
        own_record = AttendanceRecord.objects.create(
            session=self.session,
            student=self.student,
            status=AttendanceRecord.Status.PRESENT,
            marked_by=self.faculty_user,
        )
        AttendanceRecord.objects.create(
            session=self.session,
            student=self.other_student,
            status=AttendanceRecord.Status.ABSENT,
            marked_by=self.faculty_user,
        )

        self.client.force_login(self.student_user)
        response = self.client.get(
            reverse("student_attendance_history")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "attendance/student_attendance_history.html"
        )
        self.assertContains(response, "HIST001")
        self.assertContains(response, "HIST101")
        self.assertContains(response, "Present")
        self.assertEqual(
            list(response.context["records"].values_list("pk", flat=True)),
            [own_record.pk],
        )

    def test_empty_history_shows_message(self):
        self.client.force_login(self.student_user)

        response = self.client.get(
            reverse("student_attendance_history")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No attendance records found.")

    def test_unauthenticated_user_is_redirected_to_login(self):
        response = self.client.get(
            reverse("student_attendance_history")
        )

        self.assertRedirects(
            response,
            f"{reverse('login')}?next="
            f"{reverse('student_attendance_history')}",
        )

    def test_non_students_are_denied(self):
        for user in (self.faculty_user, self.admin_user):
            with self.subTest(role=user.role):
                self.client.force_login(user)
                response = self.client.get(
                    reverse("student_attendance_history")
                )
                self.assertEqual(response.status_code, 403)

    def test_student_without_profile_is_denied(self):
        unlinked_user = User.objects.create_user(
            username="unlinked_student",
            password="test-password-123",
            role=User.Role.STUDENT,
        )
        self.client.force_login(unlinked_user)

        response = self.client.get(
            reverse("student_attendance_history")
        )

        self.assertEqual(response.status_code, 403)

    def test_post_cannot_modify_attendance(self):
        record = AttendanceRecord.objects.create(
            session=self.session,
            student=self.student,
            status=AttendanceRecord.Status.PRESENT,
            marked_by=self.faculty_user,
        )
        self.client.force_login(self.student_user)

        response = self.client.post(
            reverse("student_attendance_history"),
            {"status": "ABSENT"},
        )

        self.assertEqual(response.status_code, 405)
        record.refresh_from_db()
        self.assertEqual(record.status, AttendanceRecord.Status.PRESENT)
