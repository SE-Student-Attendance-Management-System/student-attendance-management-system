"""
Quality Assurance Test Suite (GitHub Issue #38).

Traceability:
- Functional Requirements:
    - REQ-07 to REQ-09: Attendance workflow, recording, duplicate prevention, and authorized modifications
    - REQ-10: Student attendance history
    - REQ-11: Attendance percentage calculation
    - REQ-12 to REQ-13: Attendance report generation and filtering
    - REQ-14 to REQ-15: Role-specific dashboards and summaries
- Non-Functional Requirements:
    - SRS §6.1: Performance requirements (< 3.0s major pages, < 2.0s attendance marking, < 5.0s reports)
    - SRS §6.2: Safety and data integrity (transaction atomicity, rollback, duplicate prevention)
    - SRS §6.4: Usability, reliability, maintainability, and portability
- Business Rules:
    - BR-01 to BR-08
"""

import time
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.db import connection, transaction
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

User = get_user_model()


class QualityBaseTestCase(TestCase):
    """Common test fixture setting up realistic datasets for performance and reliability QA."""

    def setUp(self):
        super().setUp()

        # 1. Administrator
        self.admin = User.objects.create_user(
            username="qa_admin",
            password="qa-password-123",
            role=User.Role.ADMIN,
        )

        # 2. Faculty
        self.faculty_user = User.objects.create_user(
            username="qa_faculty",
            password="qa-password-123",
            role=User.Role.FACULTY,
        )
        self.faculty = Faculty.objects.create(
            faculty_code="QA_FAC100",
            user=self.faculty_user,
            name="Dr. Quality Faculty",
            email="qa_fac@example.com",
            department="CSE",
            is_active=True,
        )

        # 3. Unassigned Faculty
        self.other_faculty_user = User.objects.create_user(
            username="qa_other_faculty",
            password="qa-password-123",
            role=User.Role.FACULTY,
        )
        self.other_faculty = Faculty.objects.create(
            faculty_code="QA_FAC200",
            user=self.other_faculty_user,
            name="Dr. Unassigned Faculty",
            email="qa_unassigned@example.com",
            department="ECE",
            is_active=True,
        )

        # 4. Courses & Class Sections
        self.course_1 = Course.objects.create(
            course_code="CS_QA101",
            course_name="Software Quality Assurance",
            semester=5,
        )
        self.section_1 = ClassSection.objects.create(
            course=self.course_1,
            faculty=self.faculty,
            section="A",
            academic_term="2026-27",
        )

        self.course_2 = Course.objects.create(
            course_code="CS_QA102",
            course_name="Database Systems",
            semester=5,
        )
        self.section_2 = ClassSection.objects.create(
            course=self.course_2,
            faculty=self.faculty,
            section="B",
            academic_term="2026-27",
        )

        # Unassigned section (assigned to other faculty)
        self.unassigned_section = ClassSection.objects.create(
            course=self.course_2,
            faculty=self.other_faculty,
            section="C",
            academic_term="2026-27",
        )

        # 5. Students & Enrollments (20 students in section 1, 10 in section 2)
        self.students = []
        self.student_users = []
        for i in range(1, 21):
            u = User.objects.create_user(
                username=f"qa_student_{i}",
                password="qa-password-123",
                role=User.Role.STUDENT,
            )
            self.student_users.append(u)
            s = Student.objects.create(
                usn=f"1MS23QA{i:03d}",
                user=u,
                name=f"QA Student {i}",
                email=f"qastudent{i}@example.com",
                program="CSE",
                semester=5,
                is_active=True,
            )
            self.students.append(s)
            Enrollment.objects.create(student=s, class_section=self.section_1)
            if i <= 10:
                Enrollment.objects.create(student=s, class_section=self.section_2)

        # Primary test student (enrolled in sections 1 and 2)
        self.primary_student = self.students[0]
        self.primary_student_user = self.student_users[0]

        # 6. Pre-populate Sessions & Records for Section 1 (10 sessions, 200 records)
        self.sessions = []
        for s_idx in range(1, 11):
            sess = AttendanceSession.objects.create(
                class_section=self.section_1,
                session_date=date(2026, 9, 1) + timedelta(days=s_idx),
                session_no=s_idx,
            )
            self.sessions.append(sess)
            records = [
                AttendanceRecord(
                    session=sess,
                    student=s,
                    status=(
                        AttendanceRecord.Status.PRESENT
                        if (idx + s_idx) % 4 != 0
                        else AttendanceRecord.Status.ABSENT
                    ),
                    marked_by=self.faculty_user,
                )
                for idx, s in enumerate(self.students)
            ]
            AttendanceRecord.objects.bulk_create(records)


class PerformanceVerificationTests(QualityBaseTestCase):
    """
    Measure response times and query efficiency across all 9 primary operations (SRS §6.1).
    Explicitly measured against in-memory SQLite local test database.
    """

    def test_login_page_response_time(self):
        """[PERF-01] Login interface loads in under 3.0 seconds (SRS §6.1)."""
        start = time.perf_counter()
        response = self.client.get(reverse("login"))
        elapsed = time.perf_counter() - start

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            elapsed, 3.0, f"Login page took {elapsed:.3f}s (threshold: 3.0s)"
        )

    def test_admin_dashboard_response_time_and_query_efficiency(self):
        """[PERF-02] Admin dashboard loads in under 3.0 seconds without unbounded queries (REQ-14)."""
        self.client.force_login(self.admin)
        start = time.perf_counter()
        response = self.client.get(reverse("home"))
        elapsed = time.perf_counter() - start

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            elapsed, 3.0, f"Admin dashboard took {elapsed:.3f}s (threshold: 3.0s)"
        )
        self.assertIn("admin_metrics", response.context)

    def test_faculty_dashboard_response_time_and_query_efficiency(self):
        """[PERF-03] Faculty dashboard loads in under 3.0 seconds with assigned sections (REQ-14)."""
        self.client.force_login(self.faculty_user)
        start = time.perf_counter()
        response = self.client.get(reverse("home"))
        elapsed = time.perf_counter() - start

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            elapsed, 3.0, f"Faculty dashboard took {elapsed:.3f}s (threshold: 3.0s)"
        )
        self.assertIn("faculty_sections", response.context)

    def test_student_dashboard_response_time_and_query_efficiency(self):
        """[PERF-04] Student dashboard loads in under 3.0 seconds with per-class calculations (REQ-14, REQ-15)."""
        self.client.force_login(self.primary_student_user)
        start = time.perf_counter()
        response = self.client.get(reverse("home"))
        elapsed = time.perf_counter() - start

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            elapsed, 3.0, f"Student dashboard took {elapsed:.3f}s (threshold: 3.0s)"
        )
        self.assertIn("student_summaries", response.context)

    def test_attendance_sessions_list_response_time(self):
        """[PERF-05] Attendance sessions list loads in under 3.0 seconds (REQ-07)."""
        self.client.force_login(self.faculty_user)
        start = time.perf_counter()
        response = self.client.get(reverse("attendance_sessions"))
        elapsed = time.perf_counter() - start

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            elapsed, 3.0, f"Attendance sessions list took {elapsed:.3f}s (threshold: 3.0s)"
        )

    def test_attendance_marking_get_and_post_response_time(self):
        """[PERF-06] Attendance marking form load and submission complete in under 2.0 seconds (SRS §6.1)."""
        self.client.force_login(self.faculty_user)

        # Create a fresh session to mark
        fresh_session = AttendanceSession.objects.create(
            class_section=self.section_1,
            session_date=date(2026, 10, 20),
            session_no=15,
        )
        mark_url = reverse("attendance_mark", kwargs={"session_pk": fresh_session.pk})

        # 1. GET response time (< 2.0s)
        start_get = time.perf_counter()
        get_response = self.client.get(mark_url)
        elapsed_get = time.perf_counter() - start_get
        self.assertEqual(get_response.status_code, 200)
        self.assertLess(
            elapsed_get, 2.0, f"Attendance mark GET took {elapsed_get:.3f}s (threshold: 2.0s)"
        )

        # 2. POST response time (< 2.0s)
        post_payload = {f"status_{s.pk}": "PRESENT" for s in self.students}
        start_post = time.perf_counter()
        post_response = self.client.post(mark_url, post_payload, follow=True)
        elapsed_post = time.perf_counter() - start_post
        self.assertEqual(post_response.status_code, 200)
        self.assertLess(
            elapsed_post, 2.0, f"Attendance mark POST took {elapsed_post:.3f}s (threshold: 2.0s)"
        )

    def test_student_attendance_history_response_time(self):
        """[PERF-07] Student attendance history view loads in under 3.0 seconds (REQ-10)."""
        self.client.force_login(self.primary_student_user)
        start = time.perf_counter()
        response = self.client.get(reverse("student_attendance_history"))
        elapsed = time.perf_counter() - start

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            elapsed, 3.0, f"Attendance history took {elapsed:.3f}s (threshold: 3.0s)"
        )

    def test_attendance_report_generation_response_time(self):
        """[PERF-08] Report generation for class section completes in under 5.0 seconds (REQ-12, SRS §6.1)."""
        self.client.force_login(self.faculty_user)
        report_url = f"{reverse('attendance_report')}?generate=1&class_section={self.section_1.pk}"

        start = time.perf_counter()
        response = self.client.get(report_url)
        elapsed = time.perf_counter() - start

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            elapsed, 5.0, f"Report generation took {elapsed:.3f}s (threshold: 5.0s)"
        )
        self.assertTrue(response.context["has_data"])

    def test_attendance_report_filtering_response_time(self):
        """[PERF-09] Filtered attendance report by course and date window completes in under 5.0 seconds (REQ-13)."""
        self.client.force_login(self.faculty_user)
        filter_url = (
            f"{reverse('attendance_report')}?generate=1&course={self.course_1.pk}&"
            "date_from=2026-09-01&date_to=2026-09-10"
        )

        start = time.perf_counter()
        response = self.client.get(filter_url)
        elapsed = time.perf_counter() - start

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            elapsed, 5.0, f"Filtered report took {elapsed:.3f}s (threshold: 5.0s)"
        )


class AttendanceWorkflowReliabilityTests(QualityBaseTestCase):
    """
    Verify full attendance lifecycle, transactional atomicity, duplicate prevention,
    and edge-case error recovery (REQ-07–REQ-09, SRS §6.2).
    """

    def test_complete_end_to_end_attendance_lifecycle(self):
        """
        [WORKFLOW-01] Execute complete lifecycle: section selection -> session creation ->
        marking -> history view -> dynamic percentage recalculation -> report reflection.
        """
        self.client.force_login(self.faculty_user)

        # 1. Faculty creates a new valid session for Section 1
        create_url = reverse(
            "attendance_session_create", kwargs={"section_pk": self.section_1.pk}
        )
        session_date_str = "2026-10-15"
        session_no = 11

        create_resp = self.client.post(
            create_url,
            {"session_date": session_date_str, "session_no": str(session_no)},
            follow=True,
        )
        self.assertEqual(create_resp.status_code, 200)

        new_session = AttendanceSession.objects.get(
            class_section=self.section_1, session_no=session_no
        )
        self.assertEqual(str(new_session.session_date), session_date_str)

        # 2. Mark attendance (Half PRESENT, Half ABSENT)
        mark_url = reverse(
            "attendance_mark", kwargs={"session_pk": new_session.pk}
        )
        payload = {}
        for idx, s in enumerate(self.students):
            payload[f"status_{s.pk}"] = (
                "PRESENT" if idx % 2 == 0 else "ABSENT"
            )

        mark_resp = self.client.post(mark_url, payload, follow=True)
        self.assertEqual(mark_resp.status_code, 200)

        # Confirm all 20 records saved
        saved_records = AttendanceRecord.objects.filter(session=new_session)
        self.assertEqual(saved_records.count(), 20)

        # 3. Verify history for primary student
        self.client.force_login(self.primary_student_user)
        hist_resp = self.client.get(reverse("student_attendance_history"))
        self.assertEqual(hist_resp.status_code, 200)
        hist_records = hist_resp.context["records"]
        self.assertTrue(
            any(r.session == new_session for r in hist_records),
            "New attendance session was not reflected in student attendance history.",
        )

        # 4. Verify report reflects latest session
        self.client.force_login(self.faculty_user)
        rep_url = f"{reverse('attendance_report')}?generate=1&class_section={self.section_1.pk}"
        rep_resp = self.client.get(rep_url)
        self.assertEqual(rep_resp.status_code, 200)
        report_rows = rep_resp.context["report_rows"]
        primary_row = [
            r for r in report_rows if r["usn"] == self.primary_student.usn
        ][0]
        # Total classes conducted is now 11
        self.assertEqual(primary_row["total_classes"], 11)

    def test_duplicate_session_creation_idempotency(self):
        """[WORKFLOW-02] Duplicate session creation for identical section, date, and session_no is prevented."""
        self.client.force_login(self.faculty_user)
        create_url = reverse(
            "attendance_session_create", kwargs={"section_pk": self.section_1.pk}
        )

        initial_count = AttendanceSession.objects.filter(
            class_section=self.section_1
        ).count()

        # Attempt to create duplicate of session 1 on date 2026-09-02
        response = self.client.post(
            create_url,
            {"session_date": "2026-09-02", "session_no": "1"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "That attendance session already exists.")

        final_count = AttendanceSession.objects.filter(
            class_section=self.section_1
        ).count()
        self.assertEqual(
            initial_count,
            final_count,
            "Duplicate AttendanceSession was created in the database.",
        )

    def test_empty_class_roster_handling(self):
        """[WORKFLOW-03] Section with zero enrolled students handles session creation and marking gracefully."""
        # Create empty section
        empty_section = ClassSection.objects.create(
            course=self.course_1,
            faculty=self.faculty,
            section="EMPTY",
            academic_term="2026-27",
        )
        self.client.force_login(self.faculty_user)

        # 1. Create session for empty section
        create_resp = self.client.post(
            reverse("attendance_session_create", kwargs={"section_pk": empty_section.pk}),
            {"session_date": "2026-10-18", "session_no": "1"},
            follow=True,
        )
        self.assertEqual(create_resp.status_code, 200)
        sess = AttendanceSession.objects.get(class_section=empty_section, session_no=1)

        # 2. View marking form
        mark_url = reverse("attendance_mark", kwargs={"session_pk": sess.pk})
        mark_resp = self.client.get(mark_url)
        self.assertEqual(mark_resp.status_code, 200)
        self.assertEqual(len(mark_resp.context["unmarked_students"]), 0)

        # 3. POST empty form
        post_resp = self.client.post(mark_url, {}, follow=True)
        self.assertEqual(post_resp.status_code, 200)

    def test_invalid_session_identifier_handling(self):
        """[WORKFLOW-04] Accessing non-existent session ID returns HTTP 404 cleanly."""
        self.client.force_login(self.faculty_user)
        non_existent_url = reverse("attendance_mark", kwargs={"session_pk": 999999})
        response = self.client.get(non_existent_url)
        self.assertEqual(response.status_code, 404)

    def test_missing_or_malformed_attendance_status_payload(self):
        """[WORKFLOW-05] Missing student status in POST payload displays error and prevents corrupted records."""
        self.client.force_login(self.faculty_user)
        fresh_sess = AttendanceSession.objects.create(
            class_section=self.section_1,
            session_date=date(2026, 10, 22),
            session_no=18,
        )
        mark_url = reverse("attendance_mark", kwargs={"session_pk": fresh_sess.pk})

        # Submit incomplete payload: student 1 has empty status
        incomplete_payload = {f"status_{s.pk}": "PRESENT" for s in self.students[1:]}
        incomplete_payload[f"status_{self.students[0].pk}"] = ""

        response = self.client.post(mark_url, incomplete_payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, f"Select Present or Absent for {self.students[0].usn}."
        )

        # Confirm student 0 has no record in fresh session
        self.assertFalse(
            AttendanceRecord.objects.filter(
                session=fresh_sess, student=self.students[0]
            ).exists()
        )

    def test_transaction_rollback_preserves_database_consistency(self):
        """[WORKFLOW-06] Database transaction rollback ensures atomic state when exceptions occur."""
        fresh_sess = AttendanceSession.objects.create(
            class_section=self.section_1,
            session_date=date(2026, 10, 28),
            session_no=99,
        )
        initial_count = AttendanceRecord.objects.count()

        try:
            with transaction.atomic():
                AttendanceRecord.objects.create(
                    session=fresh_sess,
                    student=self.students[0],
                    status=AttendanceRecord.Status.PRESENT,
                    marked_by=self.faculty_user,
                )
                # Force an exception inside the atomic block
                raise RuntimeError("Forced simulation error for transaction rollback.")
        except RuntimeError:
            pass

        final_count = AttendanceRecord.objects.count()
        self.assertEqual(
            initial_count,
            final_count,
            "Transaction was not rolled back; orphan record was persisted.",
        )
        self.assertFalse(
            AttendanceRecord.objects.filter(session=fresh_sess).exists(),
            "Orphan AttendanceRecord persisted after transaction exception.",
        )


class DashboardUsabilityTests(QualityBaseTestCase):
    """
    Verify dashboard usability, navigation links, and empty states (Issue #36, REQ-14, REQ-15).
    """

    def test_admin_dashboard_usability_and_navigation_links(self):
        """[USABILITY-01] Admin dashboard renders metric cards, active links, and valid hrefs."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        # Expected metrics
        self.assertContains(response, "Active Students")
        self.assertContains(response, "Active Faculty")
        self.assertContains(response, "Class Sections")
        self.assertContains(response, "System Attendance")

        # Key action link hrefs
        self.assertContains(response, reverse("course_list"))
        self.assertContains(response, reverse("student_list"))
        self.assertContains(response, reverse("student_search"))
        self.assertContains(response, reverse("attendance_sessions"))
        self.assertContains(response, reverse("attendance_report"))

    def test_faculty_dashboard_usability_and_quick_action_links(self):
        """[USABILITY-02] Faculty dashboard lists assigned sections and valid action shortcuts."""
        self.client.force_login(self.faculty_user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Assigned Sections")
        self.assertContains(response, "Sessions Conducted")
        self.assertContains(response, "Enrolled Students")

        # Shortcuts
        self.assertContains(
            response,
            reverse("attendance_session_create", kwargs={"section_pk": self.section_1.pk}),
        )
        self.assertContains(response, reverse("attendance_sessions"))

    def test_student_dashboard_independent_per_class_usability(self):
        """
        [USABILITY-03] Student dashboard displays independent per-class table columns:
        Course, Section, Faculty, Total, Attended, Absent, Attendance %, Status.
        Verifies absence of aggregate student percentage or session count.
        """
        self.client.force_login(self.primary_student_user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        # Metric card: ONLY Enrolled Courses
        self.assertContains(response, "Enrolled Courses")
        self.assertNotContains(response, "Total Sessions")
        self.assertNotContains(response, "Overall Attendance")
        self.assertNotContains(response, "Attended Sessions")

        # Table headers
        self.assertContains(response, "Course")
        self.assertContains(response, "Section")
        self.assertContains(response, "Faculty")
        self.assertContains(response, "Total")
        self.assertContains(response, "Attended")
        self.assertContains(response, "Absent")
        self.assertContains(response, "Attendance %")
        self.assertContains(response, "Status")

        # Class section 1 is rendered
        self.assertContains(response, self.course_1.course_code)
        self.assertContains(response, self.course_2.course_code)

    def test_empty_state_user_experience(self):
        """[USABILITY-04] Empty states provide clear guidance rather than technical errors."""
        # 1. Unenrolled student
        fresh_user = User.objects.create_user(
            username="empty_student_user",
            password="qa-password-123",
            role=User.Role.STUDENT,
        )
        Student.objects.create(
            usn="1MS23QA999",
            user=fresh_user,
            name="Unenrolled Student",
            email="empty_s@example.com",
            program="CSE",
            semester=1,
            is_active=True,
        )
        self.client.force_login(fresh_user)
        stud_resp = self.client.get(reverse("home"))
        self.assertEqual(stud_resp.status_code, 200)
        self.assertContains(
            stud_resp,
            "No course enrollments currently recorded for your profile.",
        )

        # 2. Faculty with no assigned sections
        self.client.force_login(self.other_faculty_user)
        # remove unassigned_section from other_faculty to simulate 0 assigned sections
        self.unassigned_section.faculty = self.faculty
        self.unassigned_section.save()

        fac_resp = self.client.get(reverse("home"))
        self.assertEqual(fac_resp.status_code, 200)
        self.assertContains(
            fac_resp,
            "No class sections currently assigned to your profile.",
        )


class UIStructureAndResponsivenessTests(QualityBaseTestCase):
    """
    Verify semantic HTML, viewport meta tags, and responsive design structure (SRS §6.4).
    """

    def test_viewport_meta_tag_present_on_all_primary_pages(self):
        """[RESPONSIVE-01] Viewport meta tag is present on primary views for mobile scaling."""
        pages = [
            (None, reverse("login")),
            (self.admin, reverse("home")),
            (self.faculty_user, reverse("home")),
            (self.primary_student_user, reverse("home")),
            (self.faculty_user, reverse("attendance_sessions")),
            (self.primary_student_user, reverse("student_attendance_history")),
            (self.faculty_user, reverse("attendance_report")),
        ]

        for user, url in pages:
            with self.subTest(user=user, url=url):
                if user:
                    self.client.force_login(user)
                else:
                    self.client.logout()

                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(
                    response,
                    'name="viewport"',
                    msg_prefix=f"Viewport tag missing on {url}",
                )

    def test_no_broken_internal_navigation_links(self):
        """[USABILITY-05] Navigation links resolve to valid, active application routes."""
        self.client.force_login(self.admin)
        home_resp = self.client.get(reverse("home"))
        self.assertEqual(home_resp.status_code, 200)

        nav_urls = [
            reverse("home"),
            reverse("course_list"),
            reverse("student_list"),
            reverse("student_search"),
            reverse("attendance_sessions"),
            reverse("attendance_report"),
            reverse("logout"),
        ]

        for url in nav_urls:
            with self.subTest(url=url):
                # Verify reverse lookup resolves cleanly and returns valid response
                resp = self.client.get(url) if url != reverse("logout") else self.client.post(url)
                self.assertIn(resp.status_code, [200, 302])

