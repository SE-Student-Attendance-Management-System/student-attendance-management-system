
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

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
