"""
Security and Access-Control Verification Test Suite (GitHub Issue #37).

Traceability:
- SRS v1.0 Requirements:
    - REQ-01: User authentication and role identification
    - REQ-02: Role-based access control (Admin, Faculty, Student)
    - REQ-07: Attendance marking for authorized faculty
    - REQ-09: Authorized attendance modifications with audit logging
    - REQ-10: Student private attendance history viewing
    - REQ-12: Attendance report generation for authorized roles
    - REQ-14: Role-specific dashboard views
    - REQ-15: Role-based attendance summaries and metrics
- SRS Non-Functional Requirements:
    - SRS 6.2: Safety and data integrity (data isolation, tampering prevention)
    - SRS 6.3: Security requirements (CSRF protection, session invalidation, session fixation)
- Business Rules:
    - BR-01: Only authenticated users shall access protected system functions.
    - BR-02: Administrators shall manage system-level student, faculty, and course/class information.
    - BR-03: Faculty members shall mark attendance only for their assigned classes.
    - BR-04: Students shall be allowed to view only their own attendance records.
    - BR-05: Faculty members shall be allowed to modify attendance records only for classes assigned to them.
    - BR-08: Only authorized users shall generate attendance reports.
"""

from datetime import date
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from attendance.models import (
    AttendanceAudit,
    AttendanceRecord,
    AttendanceSession,
    ClassSection,
    Course,
    Enrollment,
    Faculty,
    Student,
)
from attendance.services import mark_attendance, update_attendance, generate_attendance_report

User = get_user_model()


class SecurityBaseTestCase(TestCase):
    """Common test fixture setting up multi-role entities and isolated data."""

    def setUp(self):
        super().setUp()

        # 1. Administrator
        self.admin_user = User.objects.create_user(
            username="sec_admin",
            password="admin-password-123",
            role=User.Role.ADMIN,
        )

        # 2. Faculty A (Assigned)
        self.faculty_user_a = User.objects.create_user(
            username="sec_faculty_a",
            password="faculty-password-123",
            role=User.Role.FACULTY,
        )
        self.faculty_a = Faculty.objects.create(
            faculty_code="SEC_FAC_A",
            user=self.faculty_user_a,
            name="Dr. Alice Faculty",
            email="faculty_a@example.com",
            department="CSE",
            is_active=True,
        )

        # 3. Faculty B (Unassigned / Peer)
        self.faculty_user_b = User.objects.create_user(
            username="sec_faculty_b",
            password="faculty-password-123",
            role=User.Role.FACULTY,
        )
        self.faculty_b = Faculty.objects.create(
            faculty_code="SEC_FAC_B",
            user=self.faculty_user_b,
            name="Dr. Bob Faculty",
            email="faculty_b@example.com",
            department="ECE",
            is_active=True,
        )

        # 4. Student 1 (Enrolled in Section A)
        self.student_user_1 = User.objects.create_user(
            username="sec_student_1",
            password="student-password-123",
            role=User.Role.STUDENT,
        )
        self.student_1 = Student.objects.create(
            usn="SEC_USN001",
            user=self.student_user_1,
            name="Charlie Student",
            email="student_1@example.com",
            program="CSE",
            semester=3,
            is_active=True,
        )

        # 5. Student 2 (Enrolled in Section B only - Peer Student)
        self.student_user_2 = User.objects.create_user(
            username="sec_student_2",
            password="student-password-123",
            role=User.Role.STUDENT,
        )
        self.student_2 = Student.objects.create(
            usn="SEC_USN002",
            user=self.student_user_2,
            name="Diana Student",
            email="student_2@example.com",
            program="ECE",
            semester=3,
            is_active=True,
        )

        # 6. Courses & Sections
        self.course_a = Course.objects.create(
            course_code="CS_SEC101",
            course_name="Security Engineering",
            semester=3,
        )
        self.section_a = ClassSection.objects.create(
            course=self.course_a,
            faculty=self.faculty_a,
            section="A",
            academic_term="2026-27",
        )
        self.enrollment_1 = Enrollment.objects.create(
            student=self.student_1,
            class_section=self.section_a,
        )

        self.course_b = Course.objects.create(
            course_code="EC_SEC201",
            course_name="Embedded Systems",
            semester=3,
        )
        self.section_b = ClassSection.objects.create(
            course=self.course_b,
            faculty=self.faculty_b,
            section="B",
            academic_term="2026-27",
        )
        self.enrollment_2 = Enrollment.objects.create(
            student=self.student_2,
            class_section=self.section_b,
        )

        # 7. Sessions & Records for Section A
        self.session_a = AttendanceSession.objects.create(
            class_section=self.section_a,
            session_date=date(2026, 10, 1),
            session_no=1,
        )
        self.record_a = AttendanceRecord.objects.create(
            session=self.session_a,
            student=self.student_1,
            status=AttendanceRecord.Status.PRESENT,
            marked_by=self.faculty_user_a,
        )

        # 8. Sessions & Records for Section B
        self.session_b = AttendanceSession.objects.create(
            class_section=self.section_b,
            session_date=date(2026, 10, 1),
            session_no=1,
        )
        self.record_b = AttendanceRecord.objects.create(
            session=self.session_b,
            student=self.student_2,
            status=AttendanceRecord.Status.PRESENT,
            marked_by=self.faculty_user_b,
        )


class AuthenticationAndSessionSecurityTests(SecurityBaseTestCase):
    """
    Verify authentication barriers, session fixation prevention,
    and post-logout session invalidation (REQ-01, BR-01, SRS 6.3).
    """

    def test_unauthenticated_requests_to_all_protected_endpoints_redirect_to_login(self):
        """Unauthenticated requests to all protected application routes must redirect (302) to login."""
        protected_urls = [
            reverse("home"),
            reverse("course_list"),
            reverse("course_create"),
            reverse("course_update", kwargs={"pk": self.course_a.pk}),
            reverse("section_update", kwargs={"pk": self.course_a.pk, "section_pk": self.section_a.pk}),
            reverse("student_list"),
            reverse("student_create"),
            reverse("student_search"),
            reverse("student_detail", kwargs={"pk": self.student_1.pk}),
            reverse("student_update", kwargs={"pk": self.student_1.pk}),
            reverse("student_attendance_history"),
            reverse("attendance_sessions"),
            reverse("attendance_session_create", kwargs={"section_pk": self.section_a.pk}),
            reverse("attendance_mark", kwargs={"session_pk": self.session_a.pk}),
            reverse("attendance_update", kwargs={"attendance_pk": self.record_a.pk}),
            reverse("attendance_report"),
            reverse("attendance_reports"),
        ]

        for target_url in protected_urls:
            with self.subTest(target_url=target_url):
                response = self.client.get(target_url)
                expected_redirect = f"{reverse('login')}?next={target_url}"
                self.assertRedirects(response, expected_redirect, status_code=302, target_status_code=200)

    def test_session_invalidation_after_logout_prevents_old_session_reuse(self):
        """A session key captured prior to logout cannot be reused to access protected pages."""
        # 1. Log in
        login_success = self.client.login(username="sec_admin", password="admin-password-123")
        self.assertTrue(login_success)

        # 2. Capture the active session ID cookie
        active_session_id = self.client.cookies["sessionid"].value

        # 3. Access a protected page to confirm valid session
        response_before = self.client.get(reverse("home"))
        self.assertEqual(response_before.status_code, 200)

        # 4. Log out using POST
        logout_response = self.client.post(reverse("logout"))
        self.assertIn(logout_response.status_code, [200, 302])

        # 5. Attempt to use the captured old session ID in a new request
        malicious_client = Client()
        malicious_client.cookies["sessionid"] = active_session_id
        response_after = malicious_client.get(reverse("home"))

        # Must redirect to login because the old session was flushed
        self.assertEqual(response_after.status_code, 302)
        self.assertTrue(response_after.url.startswith(reverse("login")))

    def test_session_key_rotation_on_login(self):
        """Logging in rotates the session key to prevent session fixation attacks."""
        client = Client()
        client.get(reverse("login"))
        pre_login_session_key = client.session.session_key

        login_success = client.login(username="sec_admin", password="admin-password-123")
        self.assertTrue(login_success)
        post_login_session_key = client.session.session_key

        self.assertNotEqual(
            pre_login_session_key,
            post_login_session_key,
            "Session key was not rotated upon successful authentication.",
        )

    def test_inactive_user_cannot_authenticate(self):
        """Inactive user accounts (is_active=False) cannot log in to the application."""
        inactive_user = User.objects.create_user(
            username="inactive_sec_user",
            password="test-password-123",
            role=User.Role.STUDENT,
            is_active=False,
        )
        login_success = self.client.login(username="inactive_sec_user", password="test-password-123")
        self.assertFalse(login_success, "Inactive user account was permitted to authenticate.")


class CSRFProtectionSecurityTests(SecurityBaseTestCase):
    """
    Verify CSRF protection on all state-changing POST endpoints (SRS 6.3).
    """

    def test_csrf_protection_rejects_post_without_token(self):
        """State-changing POST requests without a valid CSRF token return HTTP 403 Forbidden."""
        csrf_client = Client(enforce_csrf_checks=True)

        # 1. Admin endpoints
        csrf_client.force_login(self.admin_user)
        resp_course_create = csrf_client.post(
            reverse("course_create"),
            {"course_code": "CS_CSRF", "course_name": "CSRF Course", "semester": 1},
        )
        self.assertEqual(resp_course_create.status_code, 403, "CSRF check bypassed on course_create")

        resp_student_create = csrf_client.post(
            reverse("student_create"),
            {"usn": "USN_CSRF", "name": "CSRF Student", "email": "csrf@test.com", "program": "CSE", "semester": 1, "is_active": True},
        )
        self.assertEqual(resp_student_create.status_code, 403, "CSRF check bypassed on student_create")

        # 2. Faculty endpoints
        csrf_client.force_login(self.faculty_user_a)
        resp_session_create = csrf_client.post(
            reverse("attendance_session_create", kwargs={"section_pk": self.section_a.pk}),
            {"session_date": "2026-10-02", "session_no": "2"},
        )
        self.assertEqual(resp_session_create.status_code, 403, "CSRF check bypassed on attendance_session_create")

        resp_mark = csrf_client.post(
            reverse("attendance_mark", kwargs={"session_pk": self.session_a.pk}),
            {f"status_{self.student_1.pk}": "PRESENT"},
        )
        self.assertEqual(resp_mark.status_code, 403, "CSRF check bypassed on attendance_mark")

        resp_update = csrf_client.post(
            reverse("attendance_update", kwargs={"attendance_pk": self.record_a.pk}),
            {"status": "ABSENT"},
        )
        self.assertEqual(resp_update.status_code, 403, "CSRF check bypassed on attendance_update")

        # 3. Logout endpoint
        resp_logout = csrf_client.post(reverse("logout"))
        self.assertEqual(resp_logout.status_code, 403, "CSRF check bypassed on logout")


class RoleBoundaryAndDirectURLManipulationTests(SecurityBaseTestCase):
    """
    Verify server-side access barriers preventing role boundary violations
    and direct URL tampering across Admin, Faculty, and Student roles (REQ-02, BR-02, BR-03).
    """

    def test_student_denied_access_to_all_admin_and_faculty_endpoints(self):
        """Student users attempting direct GET or POST to administrative or faculty routes receive HTTP 403."""
        self.client.force_login(self.student_user_1)

        forbidden_targets = [
            # Admin-only course management
            ("GET", reverse("course_create")),
            ("POST", reverse("course_create")),
            ("GET", reverse("course_update", kwargs={"pk": self.course_a.pk})),
            ("POST", reverse("course_update", kwargs={"pk": self.course_a.pk})),
            ("GET", reverse("section_update", kwargs={"pk": self.course_a.pk, "section_pk": self.section_a.pk})),
            ("POST", reverse("section_update", kwargs={"pk": self.course_a.pk, "section_pk": self.section_a.pk})),
            # Admin-only student management
            ("GET", reverse("student_list")),
            ("GET", reverse("student_create")),
            ("POST", reverse("student_create")),
            ("GET", reverse("student_update", kwargs={"pk": self.student_1.pk})),
            ("POST", reverse("student_update", kwargs={"pk": self.student_1.pk})),
            # Faculty/Admin student profile and search
            ("GET", reverse("student_search")),
            ("GET", reverse("student_detail", kwargs={"pk": self.student_1.pk})),
            # Faculty attendance session management
            ("GET", reverse("attendance_sessions")),
            ("GET", reverse("attendance_session_create", kwargs={"section_pk": self.section_a.pk})),
            ("POST", reverse("attendance_session_create", kwargs={"section_pk": self.section_a.pk})),
            ("GET", reverse("attendance_mark", kwargs={"session_pk": self.session_a.pk})),
            ("POST", reverse("attendance_mark", kwargs={"session_pk": self.session_a.pk})),
            ("GET", reverse("attendance_update", kwargs={"attendance_pk": self.record_a.pk})),
            ("POST", reverse("attendance_update", kwargs={"attendance_pk": self.record_a.pk})),
            # Reports
            ("GET", reverse("attendance_report")),
            ("POST", reverse("attendance_report")),
        ]

        for method, url in forbidden_targets:
            with self.subTest(method=method, url=url):
                if method == "GET":
                    response = self.client.get(url)
                else:
                    response = self.client.post(url, {})
                self.assertEqual(
                    response.status_code,
                    403,
                    f"Student was not rejected with 403 Forbidden for {method} {url}",
                )

    def test_faculty_denied_access_to_admin_management_endpoints(self):
        """Faculty users attempting direct GET or POST to administrative routes receive HTTP 403."""
        self.client.force_login(self.faculty_user_a)

        admin_only_targets = [
            ("GET", reverse("course_create")),
            ("POST", reverse("course_create")),
            ("GET", reverse("course_update", kwargs={"pk": self.course_a.pk})),
            ("POST", reverse("course_update", kwargs={"pk": self.course_a.pk})),
            ("GET", reverse("section_update", kwargs={"pk": self.course_a.pk, "section_pk": self.section_a.pk})),
            ("POST", reverse("section_update", kwargs={"pk": self.course_a.pk, "section_pk": self.section_a.pk})),
            ("GET", reverse("student_list")),
            ("GET", reverse("student_create")),
            ("POST", reverse("student_create")),
            ("GET", reverse("student_update", kwargs={"pk": self.student_1.pk})),
            ("POST", reverse("student_update", kwargs={"pk": self.student_1.pk})),
        ]

        for method, url in admin_only_targets:
            with self.subTest(method=method, url=url):
                if method == "GET":
                    response = self.client.get(url)
                else:
                    response = self.client.post(url, {})
                self.assertEqual(
                    response.status_code,
                    403,
                    f"Faculty member was not rejected with 403 Forbidden for {method} {url}",
                )


class FacultySectionIsolationSecurityTests(SecurityBaseTestCase):
    """
    Verify that faculty members are strictly isolated to their assigned sections
    and cannot view, create, mark, or modify attendance for unassigned sections (BR-03, BR-05, BR-08).
    """

    def test_faculty_cannot_create_session_for_unassigned_section(self):
        """Faculty A cannot create an attendance session for Faculty B's unassigned section."""
        self.client.force_login(self.faculty_user_a)
        unassigned_url = reverse("attendance_session_create", kwargs={"section_pk": self.section_b.pk})

        # GET request
        get_response = self.client.get(unassigned_url)
        self.assertEqual(get_response.status_code, 403)

        # POST request
        post_response = self.client.post(
            unassigned_url,
            {"session_date": "2026-10-05", "session_no": "2"},
        )
        self.assertEqual(post_response.status_code, 403)

        # Confirm no session was created
        self.assertFalse(
            AttendanceSession.objects.filter(class_section=self.section_b, session_no=2).exists()
        )

    def test_faculty_cannot_mark_attendance_for_unassigned_section_session(self):
        """Faculty A cannot mark attendance for Faculty B's session via GET or POST."""
        self.client.force_login(self.faculty_user_a)
        unassigned_mark_url = reverse("attendance_mark", kwargs={"session_pk": self.session_b.pk})

        get_resp = self.client.get(unassigned_mark_url)
        self.assertEqual(get_resp.status_code, 403)

        post_resp = self.client.post(
            unassigned_mark_url,
            {f"status_{self.student_2.pk}": "ABSENT"},
        )
        self.assertEqual(post_resp.status_code, 403)

        # Verify database record was not touched
        self.record_b.refresh_from_db()
        self.assertEqual(self.record_b.status, AttendanceRecord.Status.PRESENT)

    def test_faculty_cannot_modify_attendance_record_for_unassigned_section(self):
        """Faculty A cannot edit an attendance record belonging to Faculty B's section."""
        self.client.force_login(self.faculty_user_a)
        unassigned_update_url = reverse("attendance_update", kwargs={"attendance_pk": self.record_b.pk})

        get_resp = self.client.get(unassigned_update_url)
        self.assertEqual(get_resp.status_code, 403)

        post_resp = self.client.post(
            unassigned_update_url,
            {"status": "ABSENT"},
        )
        self.assertEqual(post_resp.status_code, 403)

        self.record_b.refresh_from_db()
        self.assertEqual(self.record_b.status, AttendanceRecord.Status.PRESENT)
        self.assertFalse(AttendanceAudit.objects.filter(attendance=self.record_b).exists())

    def test_faculty_marking_ignores_injected_unenrolled_student_payload(self):
        """
        When marking attendance, injecting student IDs not enrolled in the class section
        into the POST payload is completely ignored and does not create unauthorized records.
        """
        self.client.force_login(self.faculty_user_a)
        mark_url = reverse("attendance_mark", kwargs={"session_pk": self.session_a.pk})

        # Inject student_2 who is enrolled ONLY in section_b, not section_a
        payload = {
            f"status_{self.student_1.pk}": "PRESENT",
            f"status_{self.student_2.pk}": "PRESENT",
        }
        response = self.client.post(mark_url, payload, follow=True)
        self.assertEqual(response.status_code, 200)

        # Confirm student_2 has no attendance record in session_a
        self.assertFalse(
            AttendanceRecord.objects.filter(session=self.session_a, student=self.student_2).exists(),
            "Attendance record was created for an unenrolled student via injected POST payload.",
        )

    def test_faculty_cannot_generate_report_for_unassigned_section(self):
        """Faculty A attempting to generate a report for Faculty B's section receives HTTP 403."""
        self.client.force_login(self.faculty_user_a)
        report_url = reverse("attendance_report")

        # GET tampering
        get_response = self.client.get(report_url, {"class_section": self.section_b.pk, "generate": "1"})
        self.assertEqual(get_response.status_code, 403)

        # POST tampering
        post_response = self.client.post(report_url, {"class_section": self.section_b.pk})
        self.assertEqual(post_response.status_code, 403)

    def test_faculty_filtering_by_student_usn_cannot_leak_unassigned_records(self):
        """
        Faculty A filtering reports by student USN cannot view attendance records
        for courses or sections they are not assigned to teach.
        """
        self.client.force_login(self.faculty_user_a)
        report_url = reverse("attendance_report")

        # Student 2 is only enrolled in Section B (taught by Faculty B)
        response = self.client.get(report_url, {"student_usn": self.student_2.usn, "generate": "1"})
        self.assertEqual(response.status_code, 200)

        # The report rows in context must be empty; Faculty B's section records must not leak
        report_rows = response.context["report_rows"]
        self.assertEqual(len(report_rows), 0, "Attendance records from unassigned section leaked via student USN filter.")


class StudentPrivacyAndPeerIsolationSecurityTests(SecurityBaseTestCase):
    """
    Verify student data privacy: students can access only their own records and summaries,
    cannot manipulate URLs to access peer data, and cannot access reports (REQ-04, BR-04).
    """

    def test_student_attendance_history_ignores_query_parameter_tampering(self):
        """
        Student 1 passing Student 2's identifier or USN via query parameters
        continues to receive only Student 1's attendance history.
        """
        self.client.force_login(self.student_user_1)
        history_url = reverse("student_attendance_history")

        # Tampering with query parameters
        response = self.client.get(
            history_url,
            {"student_id": self.student_2.pk, "usn": self.student_2.usn, "student_pk": self.student_2.pk},
        )
        self.assertEqual(response.status_code, 200)

        # Check records in context
        records = response.context["records"]
        for record in records:
            self.assertEqual(record.student, self.student_1)
            self.assertNotEqual(record.student, self.student_2)

        # Check rendered DOM
        self.assertContains(response, self.student_1.usn)
        self.assertNotContains(response, self.student_2.usn)

    def test_student_attendance_history_rejects_post_requests(self):
        """Student attendance history strictly rejects POST requests with HTTP 405 Method Not Allowed."""
        self.client.force_login(self.student_user_1)
        response = self.client.post(reverse("student_attendance_history"), {})
        self.assertEqual(response.status_code, 405)

    def test_student_cannot_view_peer_student_detail_profile(self):
        """Student 1 cannot access Student 2's detailed profile view at /students/<pk>/."""
        self.client.force_login(self.student_user_1)
        response = self.client.get(reverse("student_detail", kwargs={"pk": self.student_2.pk}))
        self.assertEqual(response.status_code, 403)

    def test_student_cannot_access_reports_via_get_or_post(self):
        """Student cannot access report views through any HTTP method or parameter combinations."""
        self.client.force_login(self.student_user_1)
        for url in [reverse("attendance_report"), reverse("attendance_reports")]:
            with self.subTest(url=url):
                get_resp = self.client.get(url)
                self.assertEqual(get_resp.status_code, 403)

                post_resp = self.client.post(url, {})
                self.assertEqual(post_resp.status_code, 403)


class Issue36DashboardSecurityTests(SecurityBaseTestCase):
    """
    Verify data isolation, role boundaries, and server-side controls
    on the Issue #36 role-specific dashboards (REQ-14, REQ-15, BR-01 to BR-04).
    """

    def test_student_dashboard_isolated_to_authenticated_student_profile(self):
        """Student dashboard context and template rendering strictly contain only the authenticated student's data."""
        self.client.force_login(self.student_user_1)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        summaries = response.context["student_summaries"]
        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["class_section"].pk, self.section_a.pk)

        # Peer student's section and course must not be present
        self.assertContains(response, self.course_a.course_code)
        self.assertNotContains(response, self.course_b.course_code)
        self.assertNotContains(response, self.student_2.usn)

        # Admin and faculty metric contexts must be absent
        self.assertIsNone(response.context.get("admin_metrics"))
        self.assertIsNone(response.context.get("faculty_metrics"))

    def test_student_dashboard_ignores_url_parameter_tampering(self):
        """
        Student 1 passing query parameters attempting to masquerade as Student 2 or Admin
        is strictly ignored; dashboard displays only Student 1's data.
        """
        self.client.force_login(self.student_user_1)
        tampered_url = f"{reverse('home')}?student_id={self.student_2.pk}&usn={self.student_2.usn}&role=ADMIN"
        response = self.client.get(tampered_url)
        self.assertEqual(response.status_code, 200)

        summaries = response.context["student_summaries"]
        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["class_section"].pk, self.section_a.pk)

        # Admin metrics must remain absent
        self.assertIsNone(response.context.get("admin_metrics"))
        self.assertNotContains(response, "System Attendance")

    def test_faculty_dashboard_isolated_to_assigned_sections(self):
        """Faculty dashboard context and template rendering contain only sections assigned to that faculty member."""
        self.client.force_login(self.faculty_user_a)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        faculty_sections = response.context["faculty_sections"]
        self.assertEqual(len(faculty_sections), 1)
        self.assertEqual(faculty_sections[0].pk, self.section_a.pk)

        # Faculty B's course and section must be completely absent
        self.assertContains(response, self.course_a.course_code)
        self.assertNotContains(response, self.course_b.course_code)
        self.assertNotContains(response, self.faculty_b.name)

        # Admin and student metric contexts must be absent
        self.assertIsNone(response.context.get("admin_metrics"))
        self.assertIsNone(response.context.get("student_metrics"))

    def test_admin_dashboard_metrics_and_actions_restricted_to_admin(self):
        """Admin dashboard metrics and action links are rendered only for users with the ADMIN role."""
        # 1. Admin gets metrics
        self.client.force_login(self.admin_user)
        admin_resp = self.client.get(reverse("home"))
        self.assertEqual(admin_resp.status_code, 200)
        self.assertIsNotNone(admin_resp.context.get("admin_metrics"))
        self.assertContains(admin_resp, "Administrator Dashboard")
        self.assertContains(admin_resp, "Manage Courses &amp; Class Sections")

        # 2. Faculty does NOT get admin metrics or admin action links
        self.client.force_login(self.faculty_user_a)
        fac_resp = self.client.get(reverse("home"))
        self.assertEqual(fac_resp.status_code, 200)
        self.assertIsNone(fac_resp.context.get("admin_metrics"))
        self.assertNotContains(fac_resp, "Manage Courses &amp; Class Sections")

        # 3. Student does NOT get admin metrics or admin action links
        self.client.force_login(self.student_user_1)
        stud_resp = self.client.get(reverse("home"))
        self.assertEqual(stud_resp.status_code, 200)
        self.assertIsNone(stud_resp.context.get("admin_metrics"))
        self.assertNotContains(stud_resp, "Manage Courses &amp; Class Sections")

    def test_server_side_authorization_enforced_regardless_of_template_visibility(self):
        """
        Direct HTTP requests to administration endpoints fail with 403 Forbidden
        for non-admin users, confirming authorization is enforced on the server.
        """
        self.client.force_login(self.faculty_user_a)
        resp = self.client.get(reverse("course_list"))
        self.assertEqual(resp.status_code, 403, "Server-side check failed for faculty on course_list")

        self.client.force_login(self.student_user_1)
        resp_student = self.client.get(reverse("course_list"))
        self.assertEqual(resp_student.status_code, 403, "Server-side check failed for student on course_list")


class AttendanceStatusIntegritySecurityTests(SecurityBaseTestCase):
    """
    Verify attendance status integrity: ensure unsupported statuses (e.g. LATE, EXCUSED)
    cannot be injected into marking or update workflows.
    """

    def test_marking_rejects_unsupported_status_injection(self):
        """Attendance marking rejects unsupported status values like LATE or EXCUSED."""
        self.client.force_login(self.faculty_user_a)
        mark_url = reverse("attendance_mark", kwargs={"session_pk": self.session_a.pk})

        for unsupported_status in ["LATE", "EXCUSED", "HALFDAY", "UNKNOWN"]:
            with self.subTest(status=unsupported_status):
                response = self.client.post(
                    mark_url,
                    {f"status_{self.student_1.pk}": unsupported_status},
                    follow=True,
                )
                self.assertEqual(response.status_code, 200)
                # An error message must be flashed
                self.assertContains(response, f"Select Present or Absent for {self.student_1.usn}.")

    def test_update_rejects_unsupported_status_injection(self):
        """Attendance update rejects unsupported status values and preserves database state."""
        self.client.force_login(self.faculty_user_a)
        update_url = reverse("attendance_update", kwargs={"attendance_pk": self.record_a.pk})

        for unsupported_status in ["LATE", "EXCUSED", "PENDING"]:
            with self.subTest(status=unsupported_status):
                response = self.client.post(
                    update_url,
                    {"status": unsupported_status},
                    follow=True,
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Select a valid attendance status.")

                # Confirm database record status remains unchanged
                self.record_a.refresh_from_db()
                self.assertEqual(self.record_a.status, AttendanceRecord.Status.PRESENT)


class ServiceLevelDirectInvocationSecurityTests(SecurityBaseTestCase):
    """
    Verify service-layer authorization barriers when services are invoked directly
    without view-layer mediation (defense-in-depth).
    """

    def test_service_mark_attendance_rejects_unauthorized_actors(self):
        """mark_attendance service raises PermissionDenied for student and unassigned faculty."""
        # Student actor
        with self.assertRaises(PermissionDenied):
            mark_attendance(
                session_id=self.session_a.pk,
                student_id=self.student_1.pk,
                status=AttendanceRecord.Status.PRESENT,
                marked_by=self.student_user_1,
            )

        # Unassigned Faculty actor
        with self.assertRaises(PermissionDenied):
            mark_attendance(
                session_id=self.session_a.pk,
                student_id=self.student_1.pk,
                status=AttendanceRecord.Status.PRESENT,
                marked_by=self.faculty_user_b,
            )

    def test_service_update_attendance_rejects_unauthorized_actors(self):
        """update_attendance service raises PermissionDenied for student and unassigned faculty."""
        # Student actor
        with self.assertRaises(PermissionDenied):
            update_attendance(
                attendance_id=self.record_a.pk,
                status=AttendanceRecord.Status.ABSENT,
                changed_by=self.student_user_1,
            )

        # Unassigned Faculty actor
        with self.assertRaises(PermissionDenied):
            update_attendance(
                attendance_id=self.record_a.pk,
                status=AttendanceRecord.Status.ABSENT,
                changed_by=self.faculty_user_b,
            )

    def test_service_generate_report_rejects_unauthorized_actors(self):
        """generate_attendance_report service raises PermissionDenied for student and unassigned faculty."""
        # Student actor
        with self.assertRaises(PermissionDenied):
            generate_attendance_report(user=self.student_user_1)

        # Unassigned Faculty actor requesting section B
        with self.assertRaises(PermissionDenied):
            generate_attendance_report(user=self.faculty_user_a, class_section_id=self.section_b.pk)

