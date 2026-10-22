
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.utils import timezone

from .models import (
    AttendanceAudit,
    AttendanceRecord,
    AttendanceSession,
    Enrollment,
)


@transaction.atomic
def mark_attendance(*, session_id, student_id, status, marked_by):
    """Create an attendance record for an enrolled student."""

    if status not in AttendanceRecord.Status.values:
        raise ValidationError("Invalid attendance status.")

    session = AttendanceSession.objects.select_for_update().get(
        pk=session_id
    )

    assigned_faculty_user_id = session.class_section.faculty.user_id

    if (
        marked_by.role != "ADMIN"
        and assigned_faculty_user_id != marked_by.pk
    ):
        raise PermissionDenied(
            "Only an administrator or the assigned faculty can mark attendance."
        )

    enrollment_exists = Enrollment.objects.filter(
        student_id=student_id,
        class_section_id=session.class_section_id,
    ).exists()

    if not enrollment_exists:
        raise ValidationError(
            "The student is not enrolled in this class section."
        )

    return AttendanceRecord.objects.create(
        session=session,
        student_id=student_id,
        status=status,
        marked_by=marked_by,
    )


@transaction.atomic
def update_attendance(*, attendance_id, status, changed_by):
    """Update attendance and record the status change in the audit table."""

    if status not in AttendanceRecord.Status.values:
        raise ValidationError("Invalid attendance status.")

    record = AttendanceRecord.objects.select_for_update().get(
        pk=attendance_id
    )

    if record.status == status:
        return record

    old_status = record.status
    record.status = status
    record.modified_at = timezone.now()
    record.save(update_fields=["status", "modified_at"])

    AttendanceAudit.objects.create(
        attendance=record,
        old_status=old_status,
        new_status=status,
        changed_by=changed_by,
    )

    return record
