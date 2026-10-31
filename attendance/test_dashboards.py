import time
from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from attendance.models import (
    AttendanceRecord,
    AttendanceSession,
    ClassSection,
    Course,
    Enrollment,
    Faculty,
    Student,
)

User = get_user_model()


class DashboardAuthenticationTests(TestCase):
    """
    Test authentication enforcement on dashboard and session views (REQ-14, BR-01).
    """

    def test_unauthenticated_dashboard_redirects_to_login(self):
        """Unauthenticated GET to /home/ must redirect (302) to login with next parameter."""
        response = self.client.get(reverse("home"))
        expected_redirect = f"{reverse('login')}?next={reverse('home')}"
        self.assertRedirects(response, expected_redirect, status_code=302, target_status_code=200)

    def test_unauthenticated_sessions_redirects_to_login(self):
        """Unauthenticated GET to attendance_sessions must redirect (302) to login."""
        response = self.client.get(reverse("attendance_sessions"))
        expected_redirect = f"{reverse('login')}?next={reverse('attendance_sessions')}"
        self.assertRedirects(response, expected_redirect, status_code=302, target_status_code=200)


class AdminDashboardTests(TestCase):
    """
    Test Administrator dashboard metrics calculation and template rendering (REQ-14, BR-02).
    """

    def setUp(self):
        # Admin User
        self.admin = User.objects.create_user(
            username="admin_dashboard_user",
            password="test-password-123",
            role=User.Role.ADMIN,
        )

        # Faculty: 2 active, 1 inactive
        self.faculty_user_1 = User.objects.create_user(
            username="fac_user_1", password="test-password-123", role=User.Role.FACULTY
        )
        self.faculty_1 = Faculty.objects.create(
            faculty_code="F001",
            user=self.faculty_user_1,
            name="Dr. Smith",
            email="smith@example.com",
            department="CSE",
            is_active=True,
        )

        self.faculty_user_2 = User.objects.create_user(
            username="fac_user_2", password="test-password-123", role=User.Role.FACULTY
        )
        self.faculty_2 = Faculty.objects.create(
            faculty_code="F002",
            user=self.faculty_user_2,
            name="Dr. Jones",
            email="jones@example.com",
            department="ECE",
            is_active=True,
        )

        self.faculty_user_inactive = User.objects.create_user(
            username="fac_inactive", password="test-password-123", role=User.Role.FACULTY
        )
        self.faculty_inactive = Faculty.objects.create(
            faculty_code="F003",
            user=self.faculty_user_inactive,
            name="Dr. Inactive",
            email="inactive@example.com",
            department="MECH",
            is_active=False,
        )

        # Students: 3 active, 1 inactive
        self.student_1 = Student.objects.create(
            usn="USN101",
            name="Student Active One",
            email="s1@example.com",
            program="CSE",
            semester=3,
            is_active=True,
        )
        self.student_2 = Student.objects.create(
            usn="USN102",
            name="Student Active Two",
            email="s2@example.com",
            program="CSE",
            semester=3,
            is_active=True,
        )
        self.student_3 = Student.objects.create(
            usn="USN103",
            name="Student Active Three",
            email="s3@example.com",
            program="ECE",
            semester=5,
            is_active=True,
        )
        self.student_inactive = Student.objects.create(
            usn="USN104",
            name="Student Inactive",
            email="sinactive@example.com",
            program="CSE",
            semester=3,
            is_active=False,
        )

        # Courses & Sections: 2 courses, 3 class sections
        self.course_1 = Course.objects.create(
            course_code="CS101",
            course_name="Data Structures",
            semester=3,
        )
        self.course_2 = Course.objects.create(
            course_code="EC201",
            course_name="Signals and Systems",
            semester=5,
        )

        self.sec_1 = ClassSection.objects.create(
            course=self.course_1,
            faculty=self.faculty_1,
            section="A",
            academic_term="2026-27",
        )
        self.sec_2 = ClassSection.objects.create(
            course=self.course_1,
            faculty=self.faculty_1,
            section="B",
            academic_term="2026-27",
        )
        self.sec_3 = ClassSection.objects.create(
            course=self.course_2,
            faculty=self.faculty_2,
            section="A",
            academic_term="2026-27",
        )

        # Enrollments
        Enrollment.objects.create(student=self.student_1, class_section=self.sec_1)
        Enrollment.objects.create(student=self.student_2, class_section=self.sec_1)
        Enrollment.objects.create(student=self.student_3, class_section=self.sec_3)

        # Sessions: 2 sessions for sec_1, 1 for sec_3 -> total 3 sessions
        self.session_1 = AttendanceSession.objects.create(
            class_section=self.sec_1,
            session_date=date(2026, 10, 1),
            session_no=1,
        )
        self.session_2 = AttendanceSession.objects.create(
            class_section=self.sec_1,
            session_date=date(2026, 10, 2),
            session_no=2,
        )
        self.session_3 = AttendanceSession.objects.create(
            class_section=self.sec_3,
            session_date=date(2026, 10, 3),
            session_no=1,
        )

        # Records: 5 total records: 4 Present, 1 Absent (80.0%)
        # Session 1: S1 Present, S2 Present
        AttendanceRecord.objects.create(
            session=self.session_1,
            student=self.student_1,
            status=AttendanceRecord.Status.PRESENT,
            marked_by=self.faculty_user_1,
        )
        AttendanceRecord.objects.create(
            session=self.session_1,
            student=self.student_2,
            status=AttendanceRecord.Status.PRESENT,
            marked_by=self.faculty_user_1,
        )
        # Session 2: S1 Present, S2 Absent
        AttendanceRecord.objects.create(
            session=self.session_2,
            student=self.student_1,
            status=AttendanceRecord.Status.PRESENT,
            marked_by=self.faculty_user_1,
        )
        AttendanceRecord.objects.create(
            session=self.session_2,
            student=self.student_2,
            status=AttendanceRecord.Status.ABSENT,
            marked_by=self.faculty_user_1,
        )
        # Session 3: S3 Present
        AttendanceRecord.objects.create(
            session=self.session_3,
            student=self.student_3,
            status=AttendanceRecord.Status.PRESENT,
            marked_by=self.faculty_user_2,
        )

    def test_admin_dashboard_metrics_context(self):
        """Admin dashboard computes persistent system-wide metrics accurately."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_admin"])
        self.assertFalse(response.context["is_faculty"])
        self.assertFalse(response.context["is_student"])

        metrics = response.context["admin_metrics"]
        self.assertEqual(metrics["total_students"], 3)  # Only active students
        self.assertEqual(metrics["total_faculty"], 2)   # Only active faculty
        self.assertEqual(metrics["total_courses"], 2)
        self.assertEqual(metrics["total_sections"], 3)
        self.assertEqual(metrics["total_sessions"], 3)
        self.assertEqual(metrics["total_records"], 5)
        self.assertEqual(metrics["overall_attendance_rate"], 80.0)  # 4 / 5 = 80.0%

    def test_admin_dashboard_template_rendering(self):
        """Admin dashboard displays metrics cards and administrative navigation."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administrator Dashboard")
        self.assertContains(response, "Active Students")
        self.assertContains(response, "Active Faculty")
        self.assertContains(response, "Courses")
        self.assertContains(response, "Class Sections")
        self.assertContains(response, "Sessions Held")
        self.assertContains(response, "Total Records")
        self.assertContains(response, "80.0%")
        self.assertContains(response, reverse("course_list"))
        self.assertContains(response, reverse("student_list"))
        self.assertContains(response, reverse("student_search"))
        self.assertContains(response, reverse("attendance_sessions"))
        self.assertContains(response, reverse("attendance_report"))

    def test_admin_dashboard_zero_records_empty_state(self):
        """When no attendance records exist, overall_attendance_rate is None and template renders N/A."""
        fresh_admin = User.objects.create_user(
            username="fresh_admin", password="password123", role=User.Role.ADMIN
        )
        # Delete existing records and sessions
        AttendanceRecord.objects.all().delete()
        AttendanceSession.objects.all().delete()

        self.client.force_login(fresh_admin)
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["admin_metrics"]["overall_attendance_rate"])
        self.assertContains(response, "N/A")

    def test_admin_attendance_sessions_has_admin_sections_defect_01(self):
        """Verify DEF-01 fix: attendance_sessions view passes admin_sections to context for Admin."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("attendance_sessions"))

        self.assertEqual(response.status_code, 200)
        admin_sections = response.context["admin_sections"]
        self.assertIsNotNone(admin_sections)
        self.assertEqual(admin_sections.count(), 3)
        self.assertContains(response, "Create session")


class FacultyDashboardTests(TestCase):
    """
    Test Faculty dashboard metrics calculation and template rendering (REQ-14, BR-03).
    """

    def setUp(self):
        # Faculty 1 (Assigned to 2 sections)
        self.faculty_user_1 = User.objects.create_user(
            username="faculty_lead_1", password="test-password-123", role=User.Role.FACULTY
        )
        self.faculty_1 = Faculty.objects.create(
            faculty_code="FAC301",
            user=self.faculty_user_1,
            name="Prof. Turing",
            email="turing@example.com",
            department="CSE",
        )

        # Faculty 2 (Assigned to 1 section)
        self.faculty_user_2 = User.objects.create_user(
            username="faculty_lead_2", password="test-password-123", role=User.Role.FACULTY
        )
        self.faculty_2 = Faculty.objects.create(
            faculty_code="FAC302",
            user=self.faculty_user_2,
            name="Prof. Lovelace",
            email="lovelace@example.com",
            department="CSE",
        )

        # Unassigned Faculty
        self.faculty_user_unassigned = User.objects.create_user(
            username="faculty_unassigned", password="test-password-123", role=User.Role.FACULTY
        )
        self.faculty_unassigned = Faculty.objects.create(
            faculty_code="FAC303",
            user=self.faculty_user_unassigned,
            name="Prof. Unassigned",
            email="unassigned@example.com",
            department="CSE",
        )

        # Students
        self.student_1 = Student.objects.create(
            usn="USN201", name="Alice", email="alice@test.com", program="CSE", semester=3
        )
        self.student_2 = Student.objects.create(
            usn="USN202", name="Bob", email="bob@test.com", program="CSE", semester=3
        )
        self.student_3 = Student.objects.create(
            usn="USN203", name="Charlie", email="charlie@test.com", program="CSE", semester=3
        )

        # Courses
        self.course_1 = Course.objects.create(
            course_code="CS301", course_name="Algorithms", semester=3
        )
        self.course_2 = Course.objects.create(
            course_code="CS302", course_name="Operating Systems", semester=3
        )

        # Faculty 1 sections
        self.sec_1 = ClassSection.objects.create(
            course=self.course_1, faculty=self.faculty_1, section="A", academic_term="2026-27"
        )
        self.sec_2 = ClassSection.objects.create(
            course=self.course_2, faculty=self.faculty_1, section="B", academic_term="2026-27"
        )

        # Faculty 2 section
        self.sec_other = ClassSection.objects.create(
            course=self.course_1, faculty=self.faculty_2, section="C", academic_term="2026-27"
        )

        # Enrollments: S1 & S2 in sec_1, S2 & S3 in sec_2 (total distinct students for Faculty 1 = 3)
        Enrollment.objects.create(student=self.student_1, class_section=self.sec_1)
        Enrollment.objects.create(student=self.student_2, class_section=self.sec_1)
        Enrollment.objects.create(student=self.student_2, class_section=self.sec_2)
        Enrollment.objects.create(student=self.student_3, class_section=self.sec_2)

        # Sessions for Faculty 1: 2 sessions in sec_1, 1 session in sec_2 (total 3 sessions)
        self.sess_1 = AttendanceSession.objects.create(
            class_section=self.sec_1, session_date=date(2026, 10, 1), session_no=1
        )
        self.sess_2 = AttendanceSession.objects.create(
            class_section=self.sec_1, session_date=date(2026, 10, 2), session_no=2
        )
        self.sess_3 = AttendanceSession.objects.create(
            class_section=self.sec_2, session_date=date(2026, 10, 3), session_no=1
        )

        # Attendance records for Faculty 1
        # sec_1 sess 1: S1 Present, S2 Present (2/2 = 100%)
        AttendanceRecord.objects.create(
            session=self.sess_1, student=self.student_1, status=AttendanceRecord.Status.PRESENT, marked_by=self.faculty_user_1
        )
        AttendanceRecord.objects.create(
            session=self.sess_1, student=self.student_2, status=AttendanceRecord.Status.PRESENT, marked_by=self.faculty_user_1
        )
        # sec_1 sess 2: S1 Present, S2 Absent (1/2 = 50%) -> sec_1 total: 3/4 = 75.0%
        AttendanceRecord.objects.create(
            session=self.sess_2, student=self.student_1, status=AttendanceRecord.Status.PRESENT, marked_by=self.faculty_user_1
        )
        AttendanceRecord.objects.create(
            session=self.sess_2, student=self.student_2, status=AttendanceRecord.Status.ABSENT, marked_by=self.faculty_user_1
        )
        # sec_2 sess 3: S2 Present, S3 Absent (1/2 = 50.0%)
        AttendanceRecord.objects.create(
            session=self.sess_3, student=self.student_2, status=AttendanceRecord.Status.PRESENT, marked_by=self.faculty_user_1
        )
        AttendanceRecord.objects.create(
            session=self.sess_3, student=self.student_3, status=AttendanceRecord.Status.ABSENT, marked_by=self.faculty_user_1
        )

    def test_faculty_dashboard_metrics_context(self):
        """Faculty dashboard computes section summaries, session counts, and distinct student counts."""
        self.client.force_login(self.faculty_user_1)
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_faculty"])
        metrics = response.context["faculty_metrics"]
        self.assertEqual(metrics["total_sections"], 2)
        self.assertEqual(metrics["total_sessions"], 3)
        self.assertEqual(metrics["total_students"], 3)  # Distinct students: S1, S2, S3

        sections = response.context["faculty_sections"]
        self.assertEqual(len(sections), 2)
        # sec_1: 2 enrolled, 2 sessions, 75.0% rate
        sec_1_item = [s for s in sections if s.class_section_id == self.sec_1.class_section_id][0]
        self.assertEqual(sec_1_item.enrolled_count, 2)
        self.assertEqual(sec_1_item.sessions_count, 2)
        self.assertEqual(sec_1_item.attendance_rate, 75.0)

        # sec_2: 2 enrolled, 1 session, 50.0% rate
        sec_2_item = [s for s in sections if s.class_section_id == self.sec_2.class_section_id][0]
        self.assertEqual(sec_2_item.enrolled_count, 2)
        self.assertEqual(sec_2_item.sessions_count, 1)
        self.assertEqual(sec_2_item.attendance_rate, 50.0)

    def test_faculty_dashboard_template_rendering(self):
        """Faculty dashboard renders section table with statistics and action links."""
        self.client.force_login(self.faculty_user_1)
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Faculty Dashboard")
        self.assertContains(response, "Assigned Sections")
        self.assertContains(response, "Sessions Conducted")
        self.assertContains(response, "Enrolled Students")
        self.assertContains(response, "Algorithms")
        self.assertContains(response, "Operating Systems")
        self.assertContains(response, "75.0%")
        self.assertContains(response, "50.0%")
        self.assertContains(response, reverse("attendance_sessions"))
        self.assertContains(response, reverse("student_search"))
        self.assertContains(response, reverse("attendance_report"))

    def test_faculty_dashboard_data_isolation(self):
        """Faculty member cannot see classes or metrics assigned to other faculty."""
        self.client.force_login(self.faculty_user_1)
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Section C")  # sec_other is Section C

    def test_unassigned_faculty_empty_state(self):
        """Faculty with no assigned sections sees zero metrics and clean empty state."""
        self.client.force_login(self.faculty_user_unassigned)
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        metrics = response.context["faculty_metrics"]
        self.assertEqual(metrics["total_sections"], 0)
        self.assertEqual(metrics["total_sessions"], 0)
        self.assertEqual(metrics["total_students"], 0)
        self.assertContains(response, "No class sections currently assigned to your profile.")

    def test_faculty_attendance_sessions_admin_sections_is_none(self):
        """Faculty user on attendance_sessions does not receive admin_sections context (DEF-01 isolation)."""
        self.client.force_login(self.faculty_user_1)
        response = self.client.get(reverse("attendance_sessions"))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["admin_sections"])


class StudentDashboardTests(TestCase):
    """
    Test Student dashboard independent per-class attendance calculation, peer data isolation,
    and absence of aggregated/overall attendance percentage (REQ-11, REQ-15, BR-04, BR-07).
    """

    def setUp(self):
        # Student 1 User & Profile
        self.student_user_1 = User.objects.create_user(
            username="student_user_1", password="test-password-123", role=User.Role.STUDENT
        )
        self.student_1 = Student.objects.create(
            usn="USN301",
            user=self.student_user_1,
            name="Alice Student",
            email="alice.student@example.com",
            program="CSE",
            semester=3,
        )

        # Student 2 User & Profile (Peer)
        self.student_user_2 = User.objects.create_user(
            username="student_user_2", password="test-password-123", role=User.Role.STUDENT
        )
        self.student_2 = Student.objects.create(
            usn="USN302",
            user=self.student_user_2,
            name="Bob Peer",
            email="bob.peer@example.com",
            program="CSE",
            semester=3,
        )

        # Unenrolled Student User & Profile
        self.student_user_unenrolled = User.objects.create_user(
            username="student_unenrolled", password="test-password-123", role=User.Role.STUDENT
        )
        self.student_unenrolled = Student.objects.create(
            usn="USN303",
            user=self.student_user_unenrolled,
            name="Charlie Unenrolled",
            email="charlie.unenrolled@example.com",
            program="CSE",
            semester=3,
        )

        # Faculty & Courses
        self.faculty_user = User.objects.create_user(
            username="prof_john", password="test-password-123", role=User.Role.FACULTY
        )
        self.faculty = Faculty.objects.create(
            faculty_code="FAC401",
            user=self.faculty_user,
            name="Prof. John",
            email="john@example.com",
            department="CSE",
        )

        self.course_1 = Course.objects.create(
            course_code="CS401", course_name="Database Management", semester=3
        )
        self.course_2 = Course.objects.create(
            course_code="CS402", course_name="Computer Networks", semester=3
        )

        self.sec_1 = ClassSection.objects.create(
            course=self.course_1, faculty=self.faculty, section="A", academic_term="2026-27"
        )
        self.sec_2 = ClassSection.objects.create(
            course=self.course_2, faculty=self.faculty, section="B", academic_term="2026-27"
        )

        # Enrollments: S1 in sec_1 and sec_2; S2 in sec_1
        Enrollment.objects.create(student=self.student_1, class_section=self.sec_1)
        Enrollment.objects.create(student=self.student_1, class_section=self.sec_2)
        Enrollment.objects.create(student=self.student_2, class_section=self.sec_1)

        # Sessions: 2 sessions in sec_1, 2 sessions in sec_2
        self.sess_1 = AttendanceSession.objects.create(
            class_section=self.sec_1, session_date=date(2026, 10, 1), session_no=1
        )
        self.sess_2 = AttendanceSession.objects.create(
            class_section=self.sec_1, session_date=date(2026, 10, 2), session_no=2
        )
        self.sess_3 = AttendanceSession.objects.create(
            class_section=self.sec_2, session_date=date(2026, 10, 3), session_no=1
        )
        self.sess_4 = AttendanceSession.objects.create(
            class_section=self.sec_2, session_date=date(2026, 10, 4), session_no=2
        )

        # Attendance for S1:
        # sec_1: 2 sessions, 2 Present, 0 Absent (100.0%)
        AttendanceRecord.objects.create(
            session=self.sess_1, student=self.student_1, status=AttendanceRecord.Status.PRESENT, marked_by=self.faculty_user
        )
        AttendanceRecord.objects.create(
            session=self.sess_2, student=self.student_1, status=AttendanceRecord.Status.PRESENT, marked_by=self.faculty_user
        )
        # sec_2: 2 sessions, 1 Present, 1 Absent (50.0%)
        AttendanceRecord.objects.create(
            session=self.sess_3, student=self.student_1, status=AttendanceRecord.Status.PRESENT, marked_by=self.faculty_user
        )
        AttendanceRecord.objects.create(
            session=self.sess_4, student=self.student_1, status=AttendanceRecord.Status.ABSENT, marked_by=self.faculty_user
        )

        # Attendance for S2 (Peer):
        # sec_1: 2 sessions, 0 Present, 2 Absent (0.0%)
        AttendanceRecord.objects.create(
            session=self.sess_1, student=self.student_2, status=AttendanceRecord.Status.ABSENT, marked_by=self.faculty_user
        )
        AttendanceRecord.objects.create(
            session=self.sess_2, student=self.student_2, status=AttendanceRecord.Status.ABSENT, marked_by=self.faculty_user
        )

    def test_student_dashboard_metrics_context(self):
        """Student dashboard computes independent per-class summaries without overall/aggregated metrics."""
        self.client.force_login(self.student_user_1)
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_student"])
        metrics = response.context["student_metrics"]

        # Only Enrolled Courses count is present in student metrics
        self.assertEqual(metrics["total_enrolled_courses"], 2)
        self.assertNotIn("overall_percentage", metrics)
        self.assertNotIn("total_sessions", metrics)
        self.assertNotIn("attended_sessions", metrics)

        summaries = response.context["student_summaries"]
        self.assertEqual(len(summaries), 2)

        # ClassSection 1: 2 total, 2 attended, 0 absent, 100.0%
        sec_1_summary = [s for s in summaries if s["class_section"].pk == self.sec_1.pk][0]
        self.assertEqual(sec_1_summary["total_sessions"], 2)
        self.assertEqual(sec_1_summary["attended_sessions"], 2)
        self.assertEqual(sec_1_summary["absent_sessions"], 0)
        self.assertEqual(sec_1_summary["percentage"], 100.0)
        self.assertFalse(sec_1_summary["is_low_attendance"])

        # ClassSection 2: 2 total, 1 attended, 1 absent, 50.0%, low attendance warning triggered
        sec_2_summary = [s for s in summaries if s["class_section"].pk == self.sec_2.pk][0]
        self.assertEqual(sec_2_summary["total_sessions"], 2)
        self.assertEqual(sec_2_summary["attended_sessions"], 1)
        self.assertEqual(sec_2_summary["absent_sessions"], 1)
        self.assertEqual(sec_2_summary["percentage"], 50.0)
        self.assertTrue(sec_2_summary["is_low_attendance"])

    def test_student_dashboard_template_rendering(self):
        """Student dashboard renders enrolled courses, breakdown table, and independent warnings without overall percentage."""
        self.client.force_login(self.student_user_1)
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student Dashboard")
        self.assertContains(response, "read-only access to your personal attendance records")
        self.assertContains(response, "Enrolled Courses")

        # Must NOT display or imply an overall attendance percentage or aggregated session cards
        self.assertNotContains(response, "Overall Attendance")
        self.assertNotContains(response, "Attended Sessions")

        # Must display per-class independent details
        self.assertContains(response, "Database Management")
        self.assertContains(response, "Computer Networks")
        self.assertContains(response, "100.0%")
        self.assertContains(response, "50.0%")

        # Table headers must include absent sessions
        self.assertContains(response, "Total")
        self.assertContains(response, "Attended")
        self.assertContains(response, "Absent")

        # Independent low-attendance warning: CS402 (50.0%) has warning; CS401 (100.0%) has normal
        self.assertContains(response, "Low Attendance (&lt; 75%)")
        self.assertContains(response, "Normal (&ge; 75%)")

        self.assertContains(response, reverse("student_attendance_history"))

    def test_student_dashboard_independent_class_attendance_calculation(self):
        """Attendance changes in one ClassSection strictly do not affect another ClassSection's attendance."""
        self.client.force_login(self.student_user_1)

        # Initially: sec_1 is 2/2 (100.0%), sec_2 is 1/2 (50.0%)
        res1 = self.client.get(reverse("home"))
        s1 = [s for s in res1.context["student_summaries"] if s["class_section"].pk == self.sec_1.pk][0]
        s2 = [s for s in res1.context["student_summaries"] if s["class_section"].pk == self.sec_2.pk][0]
        self.assertEqual(s1["percentage"], 100.0)
        self.assertEqual(s2["percentage"], 50.0)

        # Add a 3rd session to sec_1 where student is Absent
        sess_3_sec1 = AttendanceSession.objects.create(
            class_section=self.sec_1, session_date=date(2026, 10, 5), session_no=3
        )
        AttendanceRecord.objects.create(
            session=sess_3_sec1, student=self.student_1, status=AttendanceRecord.Status.ABSENT, marked_by=self.faculty_user
        )

        res2 = self.client.get(reverse("home"))
        s1_after = [s for s in res2.context["student_summaries"] if s["class_section"].pk == self.sec_1.pk][0]
        s2_after = [s for s in res2.context["student_summaries"] if s["class_section"].pk == self.sec_2.pk][0]

        # sec_1 changed: 2 attended / 3 total = 66.67%
        self.assertEqual(s1_after["total_sessions"], 3)
        self.assertEqual(s1_after["attended_sessions"], 2)
        self.assertEqual(s1_after["absent_sessions"], 1)
        self.assertEqual(s1_after["percentage"], 66.67)
        self.assertTrue(s1_after["is_low_attendance"])

        # sec_2 is completely unchanged: 1 attended / 2 total = 50.0%
        self.assertEqual(s2_after["total_sessions"], 2)
        self.assertEqual(s2_after["attended_sessions"], 1)
        self.assertEqual(s2_after["absent_sessions"], 1)
        self.assertEqual(s2_after["percentage"], 50.0)

        # Confirms no combined or overall student percentage exists
        self.assertNotIn("overall_percentage", res2.context["student_metrics"])

    def test_student_dashboard_peer_data_isolation(self):
        """Student sees only their personal attendance data and cannot see peer attendance."""
        self.client.force_login(self.student_user_2)
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        metrics = response.context["student_metrics"]
        self.assertEqual(metrics["total_enrolled_courses"], 1)
        self.assertNotIn("overall_percentage", metrics)

        summaries = response.context["student_summaries"]
        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["class_section"].pk, self.sec_1.pk)
        self.assertEqual(summaries[0]["attended_sessions"], 0)
        self.assertEqual(summaries[0]["absent_sessions"], 2)
        self.assertEqual(summaries[0]["percentage"], 0.0)

        self.assertNotContains(response, "Computer Networks")  # Only S1 is enrolled in CS402
        self.assertNotContains(response, "Overall Attendance")

    def test_unenrolled_student_empty_state(self):
        """Student without course enrollments sees clean empty state without overall percentage."""
        self.client.force_login(self.student_user_unenrolled)
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        metrics = response.context["student_metrics"]
        self.assertEqual(metrics["total_enrolled_courses"], 0)
        self.assertNotIn("overall_percentage", metrics)
        self.assertEqual(response.context["student_summaries"], [])

        self.assertContains(response, "No course enrollments currently recorded for your profile.")
        self.assertNotContains(response, "Overall Attendance")

    def test_student_dashboard_attendance_policy_boundary_75_percent(self):
        """
        Verify institutional attendance policy boundaries:
        - At or above 75.0% (e.g. exactly 75.0%): Normal status, meets requirement.
        - Below 75.0% (e.g. 50.0%): Low Attendance warning (< 75%).
        - Zero sessions: N/A, 'No sessions yet', not treated as low attendance.
        """
        boundary_user = User.objects.create_user(
            username="student_boundary", password="password123", role=User.Role.STUDENT
        )
        boundary_student = Student.objects.create(
            usn="USN_BND_75",
            user=boundary_user,
            name="Boundary Student",
            email="boundary@example.com",
            program="CSE",
            semester=3,
        )
        # Class with exactly 75% attendance: 4 sessions, 3 present, 1 absent
        Enrollment.objects.create(student=boundary_student, class_section=self.sec_1)
        sess_3 = AttendanceSession.objects.create(
            class_section=self.sec_1, session_date=date(2026, 10, 5), session_no=3
        )
        sess_4 = AttendanceSession.objects.create(
            class_section=self.sec_1, session_date=date(2026, 10, 6), session_no=4
        )
        AttendanceRecord.objects.create(
            session=self.sess_1, student=boundary_student, status=AttendanceRecord.Status.PRESENT, marked_by=self.faculty_user
        )
        AttendanceRecord.objects.create(
            session=self.sess_2, student=boundary_student, status=AttendanceRecord.Status.PRESENT, marked_by=self.faculty_user
        )
        AttendanceRecord.objects.create(
            session=sess_3, student=boundary_student, status=AttendanceRecord.Status.PRESENT, marked_by=self.faculty_user
        )
        AttendanceRecord.objects.create(
            session=sess_4, student=boundary_student, status=AttendanceRecord.Status.ABSENT, marked_by=self.faculty_user
        )

        # Also enroll in a course with 0 sessions
        zero_course = Course.objects.create(course_code="CS_ZERO", course_name="Zero Sessions Course", semester=3)
        zero_sec = ClassSection.objects.create(course=zero_course, faculty=self.faculty, section="Z", academic_term="2026-27")
        Enrollment.objects.create(student=boundary_student, class_section=zero_sec)

        self.client.force_login(boundary_user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        summaries = response.context["student_summaries"]
        self.assertEqual(len(summaries), 2)

        # 1. 75.0% class: Normal attendance (3/4 = 75.0%)
        item_75 = [s for s in summaries if s["class_section"].pk == self.sec_1.pk][0]
        self.assertEqual(item_75["total_sessions"], 4)
        self.assertEqual(item_75["attended_sessions"], 3)
        self.assertEqual(item_75["absent_sessions"], 1)
        self.assertEqual(item_75["percentage"], 75.0)
        self.assertFalse(item_75["is_low_attendance"])

        # 2. 0 sessions class: No sessions yet
        item_0 = [s for s in summaries if s["class_section"].pk == zero_sec.pk][0]
        self.assertEqual(item_0["total_sessions"], 0)
        self.assertEqual(item_0["attended_sessions"], 0)
        self.assertEqual(item_0["absent_sessions"], 0)
        self.assertIsNone(item_0["percentage"])
        self.assertFalse(item_0["is_low_attendance"])

        # Verify template rendering for boundary conditions
        self.assertContains(response, "75.0%")
        self.assertContains(response, "Normal (&ge; 75%)")
        self.assertContains(response, "No sessions yet")
        self.assertNotContains(response, "Low Attendance (&lt; 75%)")


class DashboardPerformanceTests(TestCase):
    """
    Test dashboard response time meets non-functional requirement (< 3.0 seconds, SRS 6.1).
    """

    def setUp(self):
        self.admin = User.objects.create_user(
            username="perf_admin", password="test-password-123", role=User.Role.ADMIN
        )
        self.faculty_user = User.objects.create_user(
            username="perf_faculty", password="test-password-123", role=User.Role.FACULTY
        )
        self.faculty = Faculty.objects.create(
            faculty_code="FAC999",
            user=self.faculty_user,
            name="Prof. Perf",
            email="perf@example.com",
            department="CSE",
        )
        self.student_user = User.objects.create_user(
            username="perf_student", password="test-password-123", role=User.Role.STUDENT
        )
        self.student = Student.objects.create(
            usn="USN999",
            user=self.student_user,
            name="Perf Student",
            email="perf_student@example.com",
            program="CSE",
            semester=3,
        )

    def test_admin_dashboard_response_time(self):
        self.client.force_login(self.admin)
        start = time.perf_counter()
        response = self.client.get(reverse("home"))
        elapsed = time.perf_counter() - start
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 3.0, f"Admin dashboard took {elapsed:.2f}s (threshold 3.0s)")

    def test_faculty_dashboard_response_time(self):
        self.client.force_login(self.faculty_user)
        start = time.perf_counter()
        response = self.client.get(reverse("home"))
        elapsed = time.perf_counter() - start
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 3.0, f"Faculty dashboard took {elapsed:.2f}s (threshold 3.0s)")

    def test_student_dashboard_response_time(self):
        self.client.force_login(self.student_user)
        start = time.perf_counter()
        response = self.client.get(reverse("home"))
        elapsed = time.perf_counter() - start
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 3.0, f"Student dashboard took {elapsed:.2f}s (threshold 3.0s)")
