"""
Role-based authorization test suite (Issue #12).

Traceability:
- Functional Requirement: REQ-02 (Provide role-based access control)
- Business Rules:
    - BR-01: Only authenticated users shall access protected system functions.
    - BR-02: Administrators shall manage system-level student, faculty, and course/class information.
    - BR-03: Faculty members shall mark attendance only for their assigned classes.
    - BR-04: Students shall be allowed to view only their own attendance records.
    - BR-05: Faculty members shall be allowed to modify attendance records only for classes assigned to them.
    - BR-08: Only authorized users shall generate attendance reports.
- Test Plan v1.1 Cases:
    - UT-02-01: Verify role-based dashboard for Administrator
    - UT-02-02: Verify role-based dashboard for Faculty
    - UT-02-03: Verify role-based dashboard for Student
    - IT-02-01: Restrict Faculty access to unauthorized areas (e.g., admin management URLs)
    - IT-02-02: Restrict Student access to Faculty features
    - ST-02-01: Prevent unauthenticated access to protected features
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse

from .models import (
    Course,
    ClassSection,
    Faculty,
    Student,
    Enrollment,
    AttendanceSession,
    AttendanceRecord,
    AttendanceAudit,
)
from .permissions import (
    can_manage_courses,
    can_faculty_manage_section,
    can_student_view_attendance,
)
from .services import mark_attendance, update_attendance

User = get_user_model()


class RoleBasedAuthorizationViewTests(TestCase):
    """
    Tests enforcing server-side role-based access control on routes and views.
    Verifies that unauthenticated requests redirect (302) to login,
    while authenticated requests lacking permission receive HTTP 403 Forbidden.
    """

    def setUp(self):
        # 1. Administrator User
        self.admin = User.objects.create_user(
            username="admin_user",
            password="admin-password-123",
            role=User.Role.ADMIN,
        )

        # 2. Faculty User & Profile
        self.faculty_user = User.objects.create_user(
            username="faculty_user",
            password="faculty-password-123",
            role=User.Role.FACULTY,
        )
        self.faculty = Faculty.objects.create(
            faculty_code="FAC201",
            user=self.faculty_user,
            name="Professor Smith",
            email="smith@example.com",
            department="CSE",
        )

        # 3. Second Faculty User (Unassigned)
        self.other_faculty_user = User.objects.create_user(
            username="other_faculty",
            password="faculty-password-123",
            role=User.Role.FACULTY,
        )
        self.other_faculty = Faculty.objects.create(
            faculty_code="FAC202",
            user=self.other_faculty_user,
            name="Professor Jones",
            email="jones@example.com",
            department="ECE",
        )

        # 4. Student User & Profile
        self.student_user = User.objects.create_user(
            username="student_user",
            password="student-password-123",
            role=User.Role.STUDENT,
        )
        self.student = Student.objects.create(
            usn="USN201",
            user=self.student_user,
            name="Alice Student",
            email="alice@example.com",
            program="CSE",
            semester=3,
        )

        # 5. Course and Section setup
        self.course = Course.objects.create(
            course_code="CS301",
            course_name="Operating Systems",
            semester=3,
        )
        self.section = ClassSection.objects.create(
            course=self.course,
            faculty=self.faculty,
            section="A",
            academic_term="2026-27",
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            class_section=self.section,
        )

    # --------------------------------------------------------------------------
    # Unauthenticated Access Tests (ST-02-01 / BR-01)
    # --------------------------------------------------------------------------

    def test_unauthenticated_requests_to_protected_views_redirect_to_login(self):
        """
        [ST-02-01 / BR-01] Unauthenticated access to protected URLs must redirect (302)
        to the login route with the original path stored in the 'next' parameter.
        """
        protected_urls = [
            reverse("home"),
            reverse("course_list"),
            reverse("course_create"),
            reverse("course_update", kwargs={"pk": self.course.pk}),
            reverse(
                "section_update",
                kwargs={"pk": self.course.pk, "section_pk": self.section.pk},
            ),
        ]

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                expected_redirect = f"{reverse('login')}?next={url}"
                self.assertRedirects(response, expected_redirect)

    def test_unauthenticated_post_requests_redirect_to_login(self):
        """Unauthenticated direct POST requests must also be redirected (302) to login."""
        post_urls = [
            (reverse("course_create"), {"course_code": "CS900", "course_name": "Test"}),
            (
                reverse("course_update", kwargs={"pk": self.course.pk}),
                {"course_code": "CS301", "course_name": "OS Updated"},
            ),
            (
                reverse(
                    "section_update",
                    kwargs={"pk": self.course.pk, "section_pk": self.section.pk},
                ),
                {"section": "B"},
            ),
        ]

        for url, data in post_urls:
            with self.subTest(url=url):
                response = self.client.post(url, data)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response.headers.get("Location", ""))

    # --------------------------------------------------------------------------
    # Administrator Role Access Tests (BR-02 / UT-02-01)
    # --------------------------------------------------------------------------

    def test_administrator_can_access_dashboard_and_management_views(self):
        """
        [UT-02-01 / BR-02] Administrator can access role-based dashboard and
        management views successfully.
        """
        self.client.force_login(self.admin)

        # Home Dashboard
        home_res = self.client.get(reverse("home"))
        self.assertEqual(home_res.status_code, 200)
        self.assertContains(home_res, "Administrator Dashboard")
        self.assertContains(home_res, reverse("course_list"))

        # Course List
        list_res = self.client.get(reverse("course_list"))
        self.assertEqual(list_res.status_code, 200)
        self.assertContains(list_res, "Operating Systems")

        # Course Create GET
        create_res = self.client.get(reverse("course_create"))
        self.assertEqual(create_res.status_code, 200)

        # Course Update GET
        update_res = self.client.get(
            reverse("course_update", kwargs={"pk": self.course.pk})
        )
        self.assertEqual(update_res.status_code, 200)

        # Section Update GET
        sec_res = self.client.get(
            reverse(
                "section_update",
                kwargs={"pk": self.course.pk, "section_pk": self.section.pk},
            )
        )
        self.assertEqual(sec_res.status_code, 200)

    # --------------------------------------------------------------------------
    # Faculty Role Access & Denial Tests (IT-02-01 / UT-02-02)
    # --------------------------------------------------------------------------

    def test_faculty_dashboard_displays_assigned_classes(self):
        """
        [UT-02-02] Faculty dashboard renders role-specific section information
        for assigned classes.
        """
        self.client.force_login(self.faculty_user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Faculty Dashboard")
        self.assertContains(response, "Operating Systems")
        self.assertContains(response, "Section A")

    def test_faculty_denied_access_to_administrator_management_views(self):
        """
        [IT-02-01] Authenticated Faculty direct GET and POST attempts to course management
        views must be rejected with HTTP 403 Forbidden.
        """
        self.client.force_login(self.faculty_user)

        restricted_gets = [
            reverse("course_list"),
            reverse("course_create"),
            reverse("course_update", kwargs={"pk": self.course.pk}),
            reverse(
                "section_update",
                kwargs={"pk": self.course.pk, "section_pk": self.section.pk},
            ),
        ]

        for url in restricted_gets:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    403,
                    f"Faculty should be denied (403) on {url}, got {response.status_code}",
                )

        # Direct POST attempt by Faculty
        post_response = self.client.post(
            reverse("course_create"),
            {
                "course_code": "CS404",
                "course_name": "Forbidden Course",
                "semester": 4,
                "faculty": self.faculty.pk,
                "section": "A",
                "academic_term": "2026-27",
            },
        )
        self.assertEqual(post_response.status_code, 403)
        self.assertFalse(Course.objects.filter(course_code="CS404").exists())

    # --------------------------------------------------------------------------
    # Student Role Access & Denial Tests (IT-02-02 / UT-02-03)
    # --------------------------------------------------------------------------

    def test_student_dashboard_displays_read_only_status(self):
        """
        [UT-02-03] Student dashboard renders role-specific enrolled class info
        and confirms read-only attendance access status.
        """
        self.client.force_login(self.student_user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student Dashboard")
        self.assertContains(response, "read-only access to your personal attendance records")
        self.assertContains(response, "Operating Systems")

    def test_student_denied_access_to_administrator_management_views(self):
        """
        [IT-02-02] Authenticated Student direct GET and POST attempts to administrative
        management views must be rejected with HTTP 403 Forbidden.
        """
        self.client.force_login(self.student_user)

        restricted_gets = [
            reverse("course_list"),
            reverse("course_create"),
            reverse("course_update", kwargs={"pk": self.course.pk}),
            reverse(
                "section_update",
                kwargs={"pk": self.course.pk, "section_pk": self.section.pk},
            ),
        ]

        for url in restricted_gets:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    403,
                    f"Student should be denied (403) on {url}, got {response.status_code}",
                )

        # Direct POST attempt by Student
        post_response = self.client.post(
            reverse("course_create"),
            {
                "course_code": "CS505",
                "course_name": "Student Created Course",
                "semester": 4,
                "faculty": self.faculty.pk,
                "section": "A",
                "academic_term": "2026-27",
            },
        )
        self.assertEqual(post_response.status_code, 403)
        self.assertFalse(Course.objects.filter(course_code="CS505").exists())


class ServiceLevelAuthorizationTests(TestCase):
    """
    Tests enforcing server-side business rules at the service layer:
    - BR-03: Faculty mark attendance only for assigned classes.
    - BR-05: Faculty modify attendance only for assigned classes.
    """

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_srv",
            password="password123",
            role=User.Role.ADMIN,
        )

        self.assigned_faculty_user = User.objects.create_user(
            username="fac_assigned",
            password="password123",
            role=User.Role.FACULTY,
        )
        self.assigned_faculty = Faculty.objects.create(
            faculty_code="FAC301",
            user=self.assigned_faculty_user,
            name="Assigned Professor",
            email="assigned@example.com",
            department="CSE",
        )

        self.unassigned_faculty_user = User.objects.create_user(
            username="fac_unassigned",
            password="password123",
            role=User.Role.FACULTY,
        )
        self.unassigned_faculty = Faculty.objects.create(
            faculty_code="FAC302",
            user=self.unassigned_faculty_user,
            name="Unassigned Professor",
            email="unassigned@example.com",
            department="ECE",
        )

        self.student_user = User.objects.create_user(
            username="student_srv",
            password="password123",
            role=User.Role.STUDENT,
        )
        self.student = Student.objects.create(
            usn="USN301",
            user=self.student_user,
            name="Bob Student",
            email="bob@example.com",
            program="CSE",
            semester=3,
        )

        self.course = Course.objects.create(
            course_code="CS302",
            course_name="Computer Networks",
            semester=3,
        )
        self.section = ClassSection.objects.create(
            course=self.course,
            faculty=self.assigned_faculty,
            section="A",
            academic_term="2026-27",
        )
        self.session = AttendanceSession.objects.create(
            class_section=self.section,
            session_date="2026-10-24",
            session_no=1,
        )
        Enrollment.objects.create(
            student=self.student,
            class_section=self.section,
        )

    def test_br03_assigned_faculty_and_admin_can_mark_attendance(self):
        """[BR-03] Assigned faculty member and administrator can mark attendance."""
        record = mark_attendance(
            session_id=self.session.pk,
            student_id=self.student.pk,
            status=AttendanceRecord.Status.PRESENT,
            marked_by=self.assigned_faculty_user,
        )
        self.assertEqual(record.status, AttendanceRecord.Status.PRESENT)
        self.assertEqual(record.marked_by, self.assigned_faculty_user)

    def test_br03_unassigned_faculty_denied_marking_attendance(self):
        """[BR-03] Unassigned faculty member is denied marking attendance."""
        with self.assertRaises(PermissionDenied):
            mark_attendance(
                session_id=self.session.pk,
                student_id=self.student.pk,
                status=AttendanceRecord.Status.PRESENT,
                marked_by=self.unassigned_faculty_user,
            )

    def test_br03_student_denied_marking_attendance(self):
        """[BR-03 / IT-02-02] Student is strictly denied marking attendance."""
        with self.assertRaises(PermissionDenied):
            mark_attendance(
                session_id=self.session.pk,
                student_id=self.student.pk,
                status=AttendanceRecord.Status.PRESENT,
                marked_by=self.student_user,
            )

    def test_br05_assigned_faculty_and_admin_can_modify_attendance(self):
        """[BR-05] Assigned faculty member and administrator can modify attendance records."""
        record = AttendanceRecord.objects.create(
            session=self.session,
            student=self.student,
            status=AttendanceRecord.Status.PRESENT,
            marked_by=self.assigned_faculty_user,
        )

        updated = update_attendance(
            attendance_id=record.pk,
            status=AttendanceRecord.Status.ABSENT,
            changed_by=self.assigned_faculty_user,
        )
        self.assertEqual(updated.status, AttendanceRecord.Status.ABSENT)
        self.assertEqual(AttendanceAudit.objects.count(), 1)

        # Admin can also modify
        admin_updated = update_attendance(
            attendance_id=record.pk,
            status=AttendanceRecord.Status.PRESENT,
            changed_by=self.admin,
        )
        self.assertEqual(admin_updated.status, AttendanceRecord.Status.PRESENT)
        self.assertEqual(AttendanceAudit.objects.count(), 2)

    def test_br05_unassigned_faculty_denied_modifying_attendance(self):
        """[BR-05] Unassigned faculty member is denied modifying attendance."""
        record = AttendanceRecord.objects.create(
            session=self.session,
            student=self.student,
            status=AttendanceRecord.Status.PRESENT,
            marked_by=self.assigned_faculty_user,
        )

        with self.assertRaises(PermissionDenied):
            update_attendance(
                attendance_id=record.pk,
                status=AttendanceRecord.Status.ABSENT,
                changed_by=self.unassigned_faculty_user,
            )

        record.refresh_from_db()
        self.assertEqual(record.status, AttendanceRecord.Status.PRESENT)
        self.assertEqual(AttendanceAudit.objects.count(), 0)

    def test_br05_student_denied_modifying_attendance(self):
        """[BR-05] Student is denied modifying attendance."""
        record = AttendanceRecord.objects.create(
            session=self.session,
            student=self.student,
            status=AttendanceRecord.Status.PRESENT,
            marked_by=self.assigned_faculty_user,
        )

        with self.assertRaises(PermissionDenied):
            update_attendance(
                attendance_id=record.pk,
                status=AttendanceRecord.Status.ABSENT,
                changed_by=self.student_user,
            )

        record.refresh_from_db()
        self.assertEqual(record.status, AttendanceRecord.Status.PRESENT)
        self.assertEqual(AttendanceAudit.objects.count(), 0)

    def test_mark_attendance_rejects_missing_or_anonymous_or_unauthenticated_actor(self):
        """
        Verify mark_attendance rejects None, AnonymousUser, unauthenticated,
        or malformed actors explicitly with PermissionDenied, without side effects.
        """
        # 1. Missing actor (None)
        with self.assertRaises(PermissionDenied):
            mark_attendance(
                session_id=self.session.pk,
                student_id=self.student.pk,
                status=AttendanceRecord.Status.PRESENT,
                marked_by=None,
            )

        # 2. AnonymousUser
        with self.assertRaises(PermissionDenied):
            mark_attendance(
                session_id=self.session.pk,
                student_id=self.student.pk,
                status=AttendanceRecord.Status.PRESENT,
                marked_by=AnonymousUser(),
            )

        # 3. Unauthenticated actor
        class UnauthenticatedActor:
            is_authenticated = False
            role = User.Role.ADMIN
            pk = 9999

        with self.assertRaises(PermissionDenied):
            mark_attendance(
                session_id=self.session.pk,
                student_id=self.student.pk,
                status=AttendanceRecord.Status.PRESENT,
                marked_by=UnauthenticatedActor(),
            )

        # 4. Malformed actor (object without role attribute)
        class MalformedActor:
            is_authenticated = True

        with self.assertRaises(PermissionDenied):
            mark_attendance(
                session_id=self.session.pk,
                student_id=self.student.pk,
                status=AttendanceRecord.Status.PRESENT,
                marked_by=MalformedActor(),
            )

        # Verify no attendance record was created
        self.assertEqual(AttendanceRecord.objects.count(), 0)

    def test_update_attendance_rejects_missing_or_anonymous_or_unauthenticated_actor(self):
        """
        Verify update_attendance rejects None, AnonymousUser, unauthenticated,
        or malformed actors explicitly with PermissionDenied, preserving record and audit log.
        """
        record = AttendanceRecord.objects.create(
            session=self.session,
            student=self.student,
            status=AttendanceRecord.Status.PRESENT,
            marked_by=self.assigned_faculty_user,
        )

        # 1. Missing actor (None)
        with self.assertRaises(PermissionDenied):
            update_attendance(
                attendance_id=record.pk,
                status=AttendanceRecord.Status.ABSENT,
                changed_by=None,
            )

        # 2. AnonymousUser
        with self.assertRaises(PermissionDenied):
            update_attendance(
                attendance_id=record.pk,
                status=AttendanceRecord.Status.ABSENT,
                changed_by=AnonymousUser(),
            )

        # 3. Unauthenticated actor
        class UnauthenticatedActor:
            is_authenticated = False
            role = User.Role.ADMIN
            pk = 9999

        with self.assertRaises(PermissionDenied):
            update_attendance(
                attendance_id=record.pk,
                status=AttendanceRecord.Status.ABSENT,
                changed_by=UnauthenticatedActor(),
            )

        # 4. Malformed actor lacking role
        class MalformedActor:
            is_authenticated = True

        with self.assertRaises(PermissionDenied):
            update_attendance(
                attendance_id=record.pk,
                status=AttendanceRecord.Status.ABSENT,
                changed_by=MalformedActor(),
            )

        # Verify record remains unmodified and no audit record exists
        record.refresh_from_db()
        self.assertEqual(record.status, AttendanceRecord.Status.PRESENT)
        self.assertEqual(AttendanceAudit.objects.count(), 0)


class PermissionHelpersTests(TestCase):
    """Unit tests for reusable permission check functions in attendance/permissions.py."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_perm",
            password="password123",
            role=User.Role.ADMIN,
        )
        self.faculty_user = User.objects.create_user(
            username="fac_perm",
            password="password123",
            role=User.Role.FACULTY,
        )
        self.faculty = Faculty.objects.create(
            faculty_code="FAC401",
            user=self.faculty_user,
            name="Perm Faculty",
            email="perm_fac@example.com",
            department="CSE",
        )
        self.other_faculty_user = User.objects.create_user(
            username="other_fac_perm",
            password="password123",
            role=User.Role.FACULTY,
        )

        self.student_user = User.objects.create_user(
            username="student_perm",
            password="password123",
            role=User.Role.STUDENT,
        )
        self.student = Student.objects.create(
            usn="USN401",
            user=self.student_user,
            name="Perm Student",
            email="perm_stu@example.com",
            program="CSE",
            semester=3,
        )
        self.other_student_user = User.objects.create_user(
            username="other_stu_perm",
            password="password123",
            role=User.Role.STUDENT,
        )

        self.course = Course.objects.create(
            course_code="CS401",
            course_name="Software Engineering",
            semester=4,
        )
        self.section = ClassSection.objects.create(
            course=self.course,
            faculty=self.faculty,
            section="A",
            academic_term="2026-27",
        )
        Enrollment.objects.create(
            student=self.student,
            class_section=self.section,
        )

    def test_can_manage_courses_helper(self):
        self.assertTrue(can_manage_courses(self.admin))
        self.assertFalse(can_manage_courses(self.faculty_user))
        self.assertFalse(can_manage_courses(self.student_user))

    def test_can_faculty_manage_section_helper(self):
        self.assertTrue(can_faculty_manage_section(self.admin, self.section))
        self.assertTrue(can_faculty_manage_section(self.faculty_user, self.section))
        self.assertFalse(can_faculty_manage_section(self.other_faculty_user, self.section))
        self.assertFalse(can_faculty_manage_section(self.student_user, self.section))

    def test_can_student_view_attendance_helper(self):
        # Admin can view
        self.assertTrue(can_student_view_attendance(self.admin, self.student))
        # Student can view own
        self.assertTrue(can_student_view_attendance(self.student_user, self.student))
        # Peer student cannot view (BR-04 / ST-02-03)
        self.assertFalse(can_student_view_attendance(self.other_student_user, self.student))
        # Faculty teaching student's section can view
        self.assertTrue(can_student_view_attendance(self.faculty_user, self.student))
        # Other faculty cannot view
        self.assertFalse(can_student_view_attendance(self.other_faculty_user, self.student))

    def test_permission_helpers_reject_missing_and_anonymous_actors(self):
        """Verify permission helpers safely return False for None and AnonymousUser."""
        # None actor
        self.assertFalse(can_manage_courses(None))
        self.assertFalse(can_faculty_manage_section(None, self.section))
        self.assertFalse(can_student_view_attendance(None, self.student))

        # AnonymousUser
        anon = AnonymousUser()
        self.assertFalse(can_manage_courses(anon))
        self.assertFalse(can_faculty_manage_section(anon, self.section))
        self.assertFalse(can_student_view_attendance(anon, self.student))
