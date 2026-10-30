"""
Tests for Attendance Report Generation (Issue #34).

Traceability:
- Functional Requirement: REQ-12 (The system shall allow authorized users to generate attendance reports)
- Business Rule: BR-08 (Only authorized users shall be allowed to generate attendance reports containing student attendance information)
- Test Plan v1.1 Cases:
    - UT-12-01: Verify report generation behavior when filtering criteria yields no results.
    - IT-12-01: Verify generated report contains all mandatory fields mapped from the database.
    - ST-12-02: Verify Faculty can generate reports for their assigned classes.
    - ST-12-03: Verify only authorized users can generate attendance reports (BR-08).
    - ST-12-04: Verify system meets performance requirements for report generation (<= 5 seconds).
    - ST-12-05: Verify Admin can filter reports by Student ID (REQ-13).
"""

import platform
import time
from datetime import date
import django
from django.db import connection
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
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
)
from .services import (
    generate_attendance_report,
    mark_attendance,
    update_attendance,
)

User = get_user_model()


class AttendanceReportBaseTestCase(TestCase):
    """Shared fixture data setup matching Test Data Inventory sections 2.1-2.5."""

    def setUp(self):
        # 1. Administrator Account (U-ADMIN-01)
        self.admin = User.objects.create_user(
            username="admin_qa_01",
            password="test-password-123",
            role=User.Role.ADMIN,
        )

        # 2. Faculty Accounts (U-FAC-01, U-FAC-02, U-FAC-03)
        self.faculty_user_1 = User.objects.create_user(
            username="faculty_qa_01",
            password="test-password-123",
            role=User.Role.FACULTY,
        )
        self.faculty_1 = Faculty.objects.create(
            faculty_code="FAC101",
            user=self.faculty_user_1,
            name="Dr. Alan Turing",
            email="alan.turing@example.test",
            department="CSE",
        )

        self.faculty_user_2 = User.objects.create_user(
            username="faculty_qa_02",
            password="test-password-123",
            role=User.Role.FACULTY,
        )
        self.faculty_2 = Faculty.objects.create(
            faculty_code="FAC102",
            user=self.faculty_user_2,
            name="Dr. Ada Lovelace",
            email="ada.lovelace@example.test",
            department="ECE",
        )

        self.faculty_user_3 = User.objects.create_user(
            username="faculty_qa_03",
            password="test-password-123",
            role=User.Role.FACULTY,
        )
        self.faculty_3 = Faculty.objects.create(
            faculty_code="FAC103",
            user=self.faculty_user_3,
            name="Dr. Grace Hopper",
            email="grace.hopper@example.test",
            department="CSE",
        )

        # 3. Student Accounts (U-STU-01, U-STU-02, U-STU-03)
        self.student_user_1 = User.objects.create_user(
            username="student_qa_01",
            password="test-password-123",
            role=User.Role.STUDENT,
        )
        self.student_1 = Student.objects.create(
            usn="USN000001",
            user=self.student_user_1,
            name="Alice Example",
            email="alice.qa01@example.test",
            phone="9876500001",
            program="CSE",
            semester=3,
        )

        self.student_user_2 = User.objects.create_user(
            username="student_qa_02",
            password="test-password-123",
            role=User.Role.STUDENT,
        )
        self.student_2 = Student.objects.create(
            usn="USN000002",
            user=self.student_user_2,
            name="Bob Example",
            email="bob.qa02@example.test",
            program="ECE",
            semester=3,
        )

        self.student_user_3 = User.objects.create_user(
            username="student_qa_03",
            password="test-password-123",
            role=User.Role.STUDENT,
        )
        self.student_3 = Student.objects.create(
            usn="USN000003",
            user=self.student_user_3,
            name="Casey Example",
            email="casey.qa03@example.test",
            phone="9876500003",
            program="CSE",
            semester=3,
        )

        self.student_4 = Student.objects.create(
            usn="USN000004",
            name="Drew Example",
            email="drew.qa04@example.test",
            program="CSE",
            semester=3,
        )

        # 4. Courses and Class Sections (C-01, C-02)
        self.course_1 = Course.objects.create(
            course_code="CS101",
            course_name="Database Systems",
            semester=3,
        )
        self.section_1 = ClassSection.objects.create(
            course=self.course_1,
            faculty=self.faculty_1,
            section="A",
            academic_term="2026-27",
        )

        self.course_2 = Course.objects.create(
            course_code="CS202",
            course_name="Data Analytics",
            semester=3,
        )
        self.section_2 = ClassSection.objects.create(
            course=self.course_2,
            faculty=self.faculty_2,
            section="B",
            academic_term="2026-27",
        )

        # 5. Enrollments
        Enrollment.objects.create(student=self.student_1, class_section=self.section_1)
        Enrollment.objects.create(student=self.student_2, class_section=self.section_1)
        Enrollment.objects.create(student=self.student_4, class_section=self.section_1)

        Enrollment.objects.create(student=self.student_1, class_section=self.section_2)
        Enrollment.objects.create(student=self.student_3, class_section=self.section_2)

        # 6. Sessions for Section 1 (CS101/A)
        self.dates_sec1 = [
            date(2026, 10, 1),
            date(2026, 10, 8),
            date(2026, 10, 15),
            date(2026, 10, 22),
            date(2026, 10, 27),
        ]
        self.sessions_sec1 = [
            AttendanceSession.objects.create(
                class_section=self.section_1,
                session_date=d,
                session_no=1,
            )
            for d in self.dates_sec1
        ]

        # S-01 in CS101/A: 4 Present, 1 Absent (80%)
        for i, sess in enumerate(self.sessions_sec1):
            st = AttendanceRecord.Status.PRESENT if i < 4 else AttendanceRecord.Status.ABSENT
            AttendanceRecord.objects.create(
                session=sess,
                student=self.student_1,
                status=st,
                marked_by=self.faculty_user_1,
            )

        # S-02 in CS101/A: 4 Absent (0%) on the first 4 sessions
        for sess in self.sessions_sec1[:4]:
            AttendanceRecord.objects.create(
                session=sess,
                student=self.student_2,
                status=AttendanceRecord.Status.ABSENT,
                marked_by=self.faculty_user_1,
            )

        # 7. Sessions for Section 2 (CS202/B)
        self.dates_sec2 = [
            date(2026, 10, 2),
            date(2026, 10, 9),
            date(2026, 10, 16),
            date(2026, 10, 23),
        ]
        self.sessions_sec2 = [
            AttendanceSession.objects.create(
                class_section=self.section_2,
                session_date=d,
                session_no=1,
            )
            for d in self.dates_sec2
        ]

        # S-03 in CS202/B: 4 Present (100%)
        for sess in self.sessions_sec2:
            AttendanceRecord.objects.create(
                session=sess,
                student=self.student_3,
                status=AttendanceRecord.Status.PRESENT,
                marked_by=self.faculty_user_2,
            )

        self.report_url = reverse("attendance_report")


class AttendanceReportAuthorizationTests(AttendanceReportBaseTestCase):
    """
    Tests enforcing server-side role-based access control (BR-08, REQ-12, ST-12-03).
    """

    def test_unauthenticated_user_redirected_to_login(self):
        """[ST-02-01 / BR-01] Unauthenticated request redirects (302) to login URL."""
        response = self.client.get(self.report_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.headers.get("Location", ""))

        # Also verify alias /attendance/reports/
        alias_url = reverse("attendance_reports")
        alias_res = self.client.get(alias_url)
        self.assertEqual(alias_res.status_code, 302)

    def test_student_denied_access_to_report_generation(self):
        """[ST-12-03 / BR-08] Authenticated Student is denied (HTTP 403 Forbidden)."""
        self.client.force_login(self.student_user_1)

        # GET request
        response = self.client.get(self.report_url)
        self.assertEqual(response.status_code, 403)

        # Direct POST attempt
        post_response = self.client.post(
            self.report_url,
            {"class_section": self.section_1.pk},
        )
        self.assertEqual(post_response.status_code, 403)

    def test_faculty_denied_access_to_unassigned_class_section(self):
        """Faculty cannot generate reports for class sections assigned to another faculty."""
        # faculty_qa_01 is assigned to section_1 (CS101/A), NOT section_2 (CS202/B)
        self.client.force_login(self.faculty_user_1)

        # Attempt to request unassigned section_2
        response = self.client.get(
            self.report_url,
            {"class_section": self.section_2.pk, "generate": "1"},
        )
        self.assertEqual(response.status_code, 403)

        # Direct POST attempt to request unassigned section_2
        post_response = self.client.post(
            self.report_url,
            {"class_section": self.section_2.pk},
        )
        self.assertEqual(post_response.status_code, 403)

    def test_faculty_with_no_assigned_classes_cannot_access_unassigned_sections(self):
        """Faculty member with no assigned classes is blocked from accessing any class section report."""
        self.client.force_login(self.faculty_user_3)
        response = self.client.get(
            self.report_url,
            {"class_section": self.section_1.pk, "generate": "1"},
        )
        self.assertEqual(response.status_code, 403)

    def test_service_level_authorization_enforced(self):
        """Service function rejects unauthorized users with PermissionDenied."""
        # Student rejected
        with self.assertRaises(PermissionDenied):
            generate_attendance_report(self.student_user_1)

        # Unauthenticated user rejected
        with self.assertRaises(PermissionDenied):
            generate_attendance_report(None)

        # Faculty querying unassigned class section rejected
        with self.assertRaises(PermissionDenied):
            generate_attendance_report(
                self.faculty_user_1,
                class_section_id=self.section_2.pk,
            )


class AttendanceReportFunctionalityTests(AttendanceReportBaseTestCase):
    """
    Tests verifying functional correctness, Appendix B field layouts, and calculations.
    """

    def test_admin_can_generate_system_scope_report(self):
        """[REQ-12] Administrator can generate report across all class sections."""
        self.client.force_login(self.admin)
        response = self.client.get(self.report_url, {"generate": "1"})

        self.assertEqual(response.status_code, 200)
        report_rows = response.context["report_rows"]
        self.assertGreater(len(report_rows), 0)

        # Verify both CS101 and CS202 appear in admin's system-wide report
        course_codes = {r["course_code"] for r in report_rows}
        self.assertIn("CS101", course_codes)
        self.assertIn("CS202", course_codes)

    def test_system_report_includes_no_records_per_enrollment(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            self.report_url,
            {"generate": "1"},
        )

        self.assertEqual(response.status_code, 200)

        rows_by_key = {
            (row["usn"], row["class_section_id"]): row
            for row in response.context["report_rows"]
        }

        # USN000001 has records in CS101/A but none in CS202/B.
        row = rows_by_key[("USN000001", self.section_2.pk)]

        self.assertEqual(row["total_classes"], 0)
        self.assertEqual(row["attended_classes"], 0)
        self.assertEqual(row["absent_classes"], 0)
        self.assertIsNone(row["percentage"])
        self.assertEqual(row["status"], "No Records")

    def test_admin_can_generate_report_for_specific_class_section(self):
        """Admin can filter and generate report for a selected class section."""
        self.client.force_login(self.admin)
        response = self.client.get(
            self.report_url,
            {"class_section": self.section_1.pk, "generate": "1"},
        )

        self.assertEqual(response.status_code, 200)
        report_rows = response.context["report_rows"]
        # Only section_1 records should be returned
        for row in report_rows:
            self.assertEqual(row["class_section_id"], self.section_1.pk)
            self.assertEqual(row["course_code"], "CS101")
            self.assertEqual(row["section"], "A")

    def test_faculty_can_generate_report_for_assigned_class(self):
        """[ST-12-02] Faculty generates report for assigned class section."""
        self.client.force_login(self.faculty_user_1)
        response = self.client.get(
            self.report_url,
            {"class_section": self.section_1.pk, "generate": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "USN000001")
        self.assertContains(response, "Alice Example")
        self.assertContains(response, "Database Systems")
        self.assertContains(response, "80.00%")

    def test_report_contains_all_appendix_b_fields(self):
        """
        [IT-12-01] Generated report contains all mandatory fields from SRS Appendix B.

        Note: SRS Appendix B (Report Requirements) and Test Plan v1.1 do not define
        an institutional percentage threshold (e.g. 75%) or specific labels for the
        'Status' column. To avoid inventing an unapproved business rule, status is
        None (rendered as '—' in the UI) for students with recorded attendance.
        """
        self.client.force_login(self.admin)
        response = self.client.get(
            self.report_url,
            {"class_section": self.section_1.pk, "generate": "1"},
        )

        self.assertEqual(response.status_code, 200)
        report_rows = response.context["report_rows"]
        alice_row = next(r for r in report_rows if r["usn"] == "USN000001")

        # Required fields in Appendix B:
        # - Student ID / USN
        # - Student Name
        # - Course ID / Course Code
        # - Course Name
        # - Total Classes
        # - Classes Attended
        # - Classes Absent
        # - Attendance Percentage
        # - Status
        self.assertEqual(alice_row["student_id"], "USN000001")
        self.assertEqual(alice_row["usn"], "USN000001")
        self.assertEqual(alice_row["student_name"], "Alice Example")
        self.assertEqual(alice_row["course_id"], "CS101")
        self.assertEqual(alice_row["course_code"], "CS101")
        self.assertEqual(alice_row["course_name"], "Database Systems")
        self.assertEqual(alice_row["total_classes"], 5)
        self.assertEqual(alice_row["attended_classes"], 4)
        self.assertEqual(alice_row["absent_classes"], 1)
        self.assertEqual(alice_row["percentage"], 80.0)
        self.assertIsNone(alice_row["status"])

        # HTML table headers checking
        self.assertContains(response, "Student ID / USN")
        self.assertContains(response, "Student Name")
        self.assertContains(response, "Course ID")
        self.assertContains(response, "Course Name")
        self.assertContains(response, "Total Classes")
        self.assertContains(response, "Attended Classes")
        self.assertContains(response, "Absent Classes")
        self.assertContains(response, "Attendance Percentage")
        self.assertContains(response, "Status")

    def test_enrolled_student_with_zero_records_in_admin_single_section_report(self):
        """
        Enrolled active students in a selected class section with zero recorded
        attendance appear in administrator single-section report with 0 totals,
        percentage=None, and status='No Records'.
        """
        self.client.force_login(self.admin)
        response = self.client.get(
            self.report_url,
            {"class_section": self.section_1.pk, "generate": "1"},
        )

        self.assertEqual(response.status_code, 200)
        rows_by_usn = {r["usn"]: r for r in response.context["report_rows"]}

        self.assertIn("USN000004", rows_by_usn)
        drew_row = rows_by_usn["USN000004"]
        self.assertEqual(drew_row["student_name"], "Drew Example")
        self.assertEqual(drew_row["total_classes"], 0)
        self.assertEqual(drew_row["attended_classes"], 0)
        self.assertEqual(drew_row["absent_classes"], 0)
        self.assertIsNone(drew_row["percentage"])
        self.assertEqual(drew_row["status"], "No Records")

        # UI renders "N/A" for percentage and "No Records" badge
        self.assertContains(response, "Drew Example")
        self.assertContains(response, "No Records")
        self.assertContains(response, "N/A")

    def test_enrolled_student_with_zero_records_in_faculty_single_section_report(self):
        """
        Enrolled active students in a faculty member's assigned class section with
        zero recorded attendance appear in the report with total=0, percentage=None,
        and status='No Records', while isolating other faculty members' students.
        """
        self.client.force_login(self.faculty_user_1)
        response = self.client.get(
            self.report_url,
            {"class_section": self.section_1.pk, "generate": "1"},
        )

        self.assertEqual(response.status_code, 200)
        rows_by_usn = {r["usn"]: r for r in response.context["report_rows"]}

        # Drew (enrolled in CS101/A with 0 records) is included
        self.assertIn("USN000004", rows_by_usn)
        drew_row = rows_by_usn["USN000004"]
        self.assertEqual(drew_row["total_classes"], 0)
        self.assertEqual(drew_row["attended_classes"], 0)
        self.assertEqual(drew_row["absent_classes"], 0)
        self.assertIsNone(drew_row["percentage"])
        self.assertEqual(drew_row["status"], "No Records")

        # Students from Faculty 2's section (Casey Example, S-03) must NOT be exposed
        self.assertNotIn("USN000003", rows_by_usn)

    def test_date_range_does_not_label_students_no_records_merely_due_to_filtered_window(self):
        """
        When a date range filter is applied, the report reflects stored records
        within that period. Students without records within that window are not
        spuriously injected or labeled 'No Records'.
        """
        self.client.force_login(self.admin)

        # Sessions for Section 1 are on Oct 1, 8, 15, 22, 27.
        # Query only Oct 1 to Oct 8 (2 sessions).
        response = self.client.get(
            self.report_url,
            {
                "class_section": self.section_1.pk,
                "date_from": "2026-10-01",
                "date_to": "2026-10-08",
                "generate": "1",
            },
        )

        self.assertEqual(response.status_code, 200)
        rows_by_usn = {r["usn"]: r for r in response.context["report_rows"]}

        # S-01 and S-02 had records in this window; Drew (S-04) had no records
        self.assertIn("USN000001", rows_by_usn)
        self.assertIn("USN000002", rows_by_usn)
        self.assertNotIn("USN000004", rows_by_usn)

        # Verify S-01's stats for this 2-session window (2 Present out of 2)
        self.assertEqual(rows_by_usn["USN000001"]["total_classes"], 2)
        self.assertEqual(rows_by_usn["USN000001"]["attended_classes"], 2)
        self.assertEqual(rows_by_usn["USN000001"]["percentage"], 100.0)

    def test_attendance_percentage_calculations(self):
        """Verify calculations for 80%, 0%, 100%, and unrecorded students."""
        self.client.force_login(self.admin)
        response = self.client.get(
            self.report_url,
            {"class_section": self.section_1.pk, "generate": "1"},
        )
        rows_by_usn = {r["usn"]: r for r in response.context["report_rows"]}

        # S-01: 4 Present, 1 Absent out of 5 -> 80.00%
        self.assertEqual(rows_by_usn["USN000001"]["total_classes"], 5)
        self.assertEqual(rows_by_usn["USN000001"]["attended_classes"], 4)
        self.assertEqual(rows_by_usn["USN000001"]["absent_classes"], 1)
        self.assertEqual(rows_by_usn["USN000001"]["percentage"], 80.0)

        # S-02: 0 Present, 4 Absent out of 4 -> 0.00%
        self.assertEqual(rows_by_usn["USN000002"]["total_classes"], 4)
        self.assertEqual(rows_by_usn["USN000002"]["attended_classes"], 0)
        self.assertEqual(rows_by_usn["USN000002"]["absent_classes"], 4)
        self.assertEqual(rows_by_usn["USN000002"]["percentage"], 0.0)

        # S-04: Enrolled in CS101/A, but 0 recorded sessions
        self.assertEqual(rows_by_usn["USN000004"]["total_classes"], 0)
        self.assertEqual(rows_by_usn["USN000004"]["attended_classes"], 0)
        self.assertEqual(rows_by_usn["USN000004"]["absent_classes"], 0)
        self.assertIsNone(rows_by_usn["USN000004"]["percentage"])
        self.assertEqual(rows_by_usn["USN000004"]["status"], "No Records")

        # Section 2: S-03: 4 Present out of 4 -> 100.00%
        sec2_res = self.client.get(
            self.report_url,
            {"class_section": self.section_2.pk, "generate": "1"},
        )
        sec2_rows = {r["usn"]: r for r in sec2_res.context["report_rows"]}
        self.assertEqual(sec2_rows["USN000003"]["total_classes"], 4)
        self.assertEqual(sec2_rows["USN000003"]["attended_classes"], 4)
        self.assertEqual(sec2_rows["USN000003"]["absent_classes"], 0)
        self.assertEqual(sec2_rows["USN000003"]["percentage"], 100.0)

    def test_report_reflects_persistent_records_and_updates(self):
        """Attendance modifications immediately reflect in subsequent reports."""
        self.client.force_login(self.admin)

        # Modify S-01's last record from ABSENT to PRESENT
        s1_last_record = AttendanceRecord.objects.filter(
            student=self.student_1,
            session=self.sessions_sec1[-1],
        ).first()

        self.assertEqual(s1_last_record.status, AttendanceRecord.Status.ABSENT)
        update_attendance(
            attendance_id=s1_last_record.pk,
            status=AttendanceRecord.Status.PRESENT,
            changed_by=self.admin,
        )

        response = self.client.get(
            self.report_url,
            {"class_section": self.section_1.pk, "generate": "1"},
        )
        rows_by_usn = {r["usn"]: r for r in response.context["report_rows"]}

        # S-01 now has 5 Present out of 5 -> 100.00%
        self.assertEqual(rows_by_usn["USN000001"]["attended_classes"], 5)
        self.assertEqual(rows_by_usn["USN000001"]["absent_classes"], 0)
        self.assertEqual(rows_by_usn["USN000001"]["percentage"], 100.0)

    def test_filter_by_course(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.report_url, {"course": self.course_1.pk, "generate": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["report_rows"])
        self.assertEqual({r["course_code"] for r in response.context["report_rows"]}, {"CS101"})

    def test_filter_by_course_and_class_section(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.report_url, {"course": self.course_1.pk, "class_section": self.section_1.pk, "generate": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["report_rows"])
        self.assertEqual({r["class_section_id"] for r in response.context["report_rows"]}, {self.section_1.pk})

    def test_rejects_mismatched_course_and_class_section(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.report_url, {"course": self.course_2.pk, "class_section": self.section_1.pk, "generate": "1"})
        self.assertFalse(r.context["report_rows"])
        self.assertIn("course", r.context["form"].errors)

    def test_faculty_cannot_filter_by_unassigned_course(self):
        self.client.force_login(self.faculty_user_1)
        r=self.client.get(self.report_url, {"course": self.course_2.pk, "generate": "1"})
        self.assertFalse(r.context["report_rows"])
        self.assertIn("course", r.context["form"].errors)

    def test_filter_by_student_usn(self):
        """[ST-12-05] Report can be filtered by specific Student ID / USN."""
        self.client.force_login(self.admin)
        response = self.client.get(
            self.report_url,
            {"student_id": "USN000001", "generate": "1"},
        )

        self.assertEqual(response.status_code, 200)
        report_rows = response.context["report_rows"]
        self.assertEqual(len(report_rows), 1)
        self.assertEqual(report_rows[0]["usn"], "USN000001")
        self.assertContains(response, "Alice Example")
        self.assertNotContains(response, "Bob Example")

    def test_filter_by_date_range(self):
        """Report filters attendance records within the selected date boundaries."""
        self.client.force_login(self.admin)

        # Filter sessions between Oct 1 and Oct 15 (3 sessions)
        response = self.client.get(
            self.report_url,
            {
                "class_section": self.section_1.pk,
                "date_from": "2026-10-01",
                "date_to": "2026-10-15",
                "generate": "1",
            },
        )

        self.assertEqual(response.status_code, 200)
        rows_by_usn = {r["usn"]: r for r in response.context["report_rows"]}

        # S-01 had 3 sessions within this range, all Present -> 3/3 = 100%
        self.assertEqual(rows_by_usn["USN000001"]["total_classes"], 3)
        self.assertEqual(rows_by_usn["USN000001"]["attended_classes"], 3)
        self.assertEqual(rows_by_usn["USN000001"]["percentage"], 100.0)


class AttendanceReportValidationAndEmptyStateTests(AttendanceReportBaseTestCase):
    """
    Tests verifying empty result messages and invalid criteria handling (UT-12-01).
    """

    def test_empty_results_when_criteria_yields_no_records(self):
        """[UT-12-01] Future date range with no attendance displays appropriate validation message."""
        self.client.force_login(self.admin)
        response = self.client.get(
            self.report_url,
            {
                "date_from": "2099-01-01",
                "date_to": "2099-12-31",
                "generate": "1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["report_rows"]), 0)
        self.assertContains(
            response,
            "No attendance data available for the selected criteria.",
        )

    def test_empty_results_for_class_section_without_attendance(self):
        """A class section with zero recorded sessions and no enrollments displays the empty state message."""
        new_course = Course.objects.create(
            course_code="CS999",
            course_name="Future Systems",
            semester=4,
        )
        new_section = ClassSection.objects.create(
            course=new_course,
            faculty=self.faculty_1,
            section="Z",
            academic_term="2026-27",
        )

        self.client.force_login(self.faculty_user_1)
        response = self.client.get(
            self.report_url,
            {"class_section": new_section.pk, "generate": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["report_rows"]), 0)
        self.assertContains(
            response,
            "No attendance data available for the selected criteria.",
        )

    def test_nonexistent_class_section_id_produces_validation_error(self):
        """Selecting a non-existent class section ID produces validation error without broadening scope."""
        self.client.force_login(self.admin)
        response = self.client.get(
            self.report_url,
            {"class_section": "999999", "generate": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("class_section", response.context["form"].errors)
        self.assertContains(response, "Selected class section does not exist.")
        self.assertEqual(len(response.context["report_rows"]), 0)

        # Also verify for faculty user
        self.client.force_login(self.faculty_user_1)
        fac_response = self.client.get(
            self.report_url,
            {"class_section": "999999", "generate": "1"},
        )
        self.assertEqual(fac_response.status_code, 200)
        self.assertIn("class_section", fac_response.context["form"].errors)
        self.assertContains(fac_response, "Selected class section does not exist.")
        self.assertEqual(len(fac_response.context["report_rows"]), 0)

    def test_malformed_class_section_id_produces_validation_error(self):
        """Submitting a non-numeric/malformed class section ID produces a validation error."""
        self.client.force_login(self.admin)
        response = self.client.get(
            self.report_url,
            {"class_section": "not-an-id", "generate": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("class_section", response.context["form"].errors)
        self.assertContains(response, "Select a valid class section.")
        self.assertEqual(len(response.context["report_rows"]), 0)

    def test_faculty_member_selecting_unassigned_section_returns_403(self):
        """Faculty member attempting to select an unassigned class section is denied with HTTP 403."""
        # faculty_qa_01 is assigned to section_1 (CS101/A), not section_2 (CS202/B)
        self.client.force_login(self.faculty_user_1)
        response = self.client.get(
            self.report_url,
            {"class_section": str(self.section_2.pk), "generate": "1"},
        )
        self.assertEqual(response.status_code, 403)

    def test_assigned_faculty_member_selecting_own_section_succeeds(self):
        """Faculty member selecting their assigned class section successfully generates report."""
        self.client.force_login(self.faculty_user_1)
        response = self.client.get(
            self.report_url,
            {"class_section": str(self.section_1.pk), "generate": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.context["report_rows"]), 0)
        for row in response.context["report_rows"]:
            self.assertEqual(row["class_section_id"], self.section_1.pk)

    def test_empty_results_for_nonexistent_student_usn(self):
        """Querying a non-existent student USN displays empty state message."""
        self.client.force_login(self.admin)
        response = self.client.get(
            self.report_url,
            {"student_id": "NONEXISTENT99", "generate": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["report_rows"]), 0)
        self.assertContains(
            response,
            "No attendance data available for the selected criteria.",
        )

    def test_invalid_criteria_start_date_after_end_date(self):
        """Submitting a date range where start date > end date produces validation error."""
        self.client.force_login(self.admin)
        response = self.client.get(
            self.report_url,
            {
                "date_from": "2026-10-30",
                "date_to": "2026-10-01",
                "generate": "1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("date_from", response.context["form"].errors)
        self.assertContains(response, "Start date cannot be after end date.")
        self.assertEqual(len(response.context["report_rows"]), 0)

    def test_invalid_date_format_rejected(self):
        """Malformed date string produces form validation error."""
        self.client.force_login(self.admin)
        response = self.client.get(
            self.report_url,
            {"date_from": "not-a-valid-date", "generate": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("date_from", response.context["form"].errors)
        self.assertEqual(len(response.context["report_rows"]), 0)

    def test_invalid_student_id_format_rejected(self):
        """Student ID with special characters or exceeding 15 chars is rejected."""
        self.client.force_login(self.admin)

        # Over 15 characters
        response_len = self.client.get(
            self.report_url,
            {"student_id": "USN0123456789ABCDE", "generate": "1"},
        )
        self.assertIn("student_id", response_len.context["form"].errors)

        # Special characters
        response_char = self.client.get(
            self.report_url,
            {"student_id": "USN@123!", "generate": "1"},
        )
        self.assertIn("student_id", response_char.context["form"].errors)


class AttendanceReportIsolationTests(AttendanceReportBaseTestCase):
    """
    Tests ensuring data isolation between class sections and students.
    """

    def test_section_isolation(self):
        """Attendance records from one section do not leak into another section report."""
        self.client.force_login(self.admin)

        # Generate for Section 1 (CS101/A)
        res_sec1 = self.client.get(
            self.report_url,
            {"class_section": self.section_1.pk, "generate": "1"},
        )
        usns_sec1 = {r["usn"] for r in res_sec1.context["report_rows"]}

        # S-03 is only in Section 2, must NOT be in Section 1
        self.assertNotIn("USN000003", usns_sec1)

        # Generate for Section 2 (CS202/B)
        res_sec2 = self.client.get(
            self.report_url,
            {"class_section": self.section_2.pk, "generate": "1"},
        )
        usns_sec2 = {r["usn"] for r in res_sec2.context["report_rows"]}

        # S-02 and S-04 are only in Section 1, must NOT be in Section 2
        self.assertNotIn("USN000002", usns_sec2)
        self.assertNotIn("USN000004", usns_sec2)


class AttendanceReportPerformanceTests(AttendanceReportBaseTestCase):
    """
    Tests verifying the 5-second report generation requirement (ST-12-04 / REQ-12).
    """

    def test_normal_sized_report_generation_under_five_seconds(self):
        """
        [ST-12-04] Measure report generation elapsed time for a 500-record dataset.
        Must complete and render in less than 5.0 seconds under normal conditions.
        """
        # Create a dedicated course and section for the performance dataset
        perf_course = Course.objects.create(
            course_code="PERF100",
            course_name="Performance Benchmarking",
            semester=5,
        )
        perf_section = ClassSection.objects.create(
            course=perf_course,
            faculty=self.faculty_1,
            section="P",
            academic_term="2026-27",
        )

        # Create 20 students
        perf_students = [
            Student.objects.create(
                usn=f"PSTU{i:04d}",
                name=f"Perf Student {i}",
                email=f"perf{i}@example.test",
                program="CSE",
                semester=5,
            )
            for i in range(20)
        ]

        for s in perf_students:
            Enrollment.objects.create(student=s, class_section=perf_section)

        # Create 25 sessions (20 students x 25 sessions = 500 records)
        perf_sessions = [
            AttendanceSession.objects.create(
                class_section=perf_section,
                session_date=date(2026, 9, 1 + (j % 28)),
                session_no=(j // 28) + 1,
            )
            for j in range(25)
        ]

        records_to_create = []
        for s in perf_students:
            for k, sess in enumerate(perf_sessions):
                st = (
                    AttendanceRecord.Status.PRESENT
                    if (k % 3 != 0)
                    else AttendanceRecord.Status.ABSENT
                )
                records_to_create.append(
                    AttendanceRecord(
                        session=sess,
                        student=s,
                        status=st,
                        marked_by=self.faculty_user_1,
                    )
                )

        AttendanceRecord.objects.bulk_create(records_to_create)
        self.assertEqual(len(records_to_create), 500)

        self.client.force_login(self.admin)

        start_time = time.perf_counter()
        response = self.client.get(
            self.report_url,
            {"class_section": perf_section.pk, "generate": "1"},
        )
        elapsed = time.perf_counter() - start_time

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["report_rows"]), 20)

        # Output explicit empirical performance evidence for audit
        import sys
        sys.stderr.write(
            f"\n[ST-12-04 Performance Evidence] Dataset: 500 AttendanceRecord rows "
            f"(20 students x 25 sessions) in ClassSection {perf_section.pk}; "
            f"Database engine: {connection.settings_dict.get('ENGINE')}; "
            f"Python: {platform.python_version()}; "
            f"Django: {django.get_version()}; "
            f"Elapsed time: {elapsed:.4f}s (SRS Target: <= 5.0000s)\n"
        )

        self.assertLess(
            elapsed,
            5.0,
            f"Report generation took {elapsed:.3f}s, which exceeds the 5-second target.",
        )
