from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import Count, Q
from django.db import transaction
from django.utils import timezone

from .models import (
    AttendanceAudit,
    AttendanceRecord,
    AttendanceSession,
    ClassSection,
    Enrollment,
)


@transaction.atomic
def mark_attendance(*, session_id, student_id, status, marked_by):
    """Create an attendance record for an enrolled student."""

    if status not in AttendanceRecord.Status.values:
        raise ValidationError("Invalid attendance status.")

    if (
        not marked_by
        or not getattr(marked_by, "is_authenticated", False)
        or not hasattr(marked_by, "role")
    ):
        raise PermissionDenied(
            "Only an administrator or the assigned faculty can mark attendance."
        )

    session = AttendanceSession.objects.select_for_update().get(
        pk=session_id
    )

    assigned_faculty_user_id = session.class_section.faculty.user_id

    if (
        marked_by.role != "ADMIN"
        and assigned_faculty_user_id != getattr(marked_by, "pk", None)
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

    if (
        not changed_by
        or not getattr(changed_by, "is_authenticated", False)
        or not hasattr(changed_by, "role")
    ):
        raise PermissionDenied(
            "Only an administrator or the assigned faculty can modify attendance records."
        )

    record = AttendanceRecord.objects.select_for_update().get(
        pk=attendance_id
    )

    assigned_faculty_user_id = record.session.class_section.faculty.user_id

    if (
        changed_by.role != "ADMIN"
        and assigned_faculty_user_id != getattr(changed_by, "pk", None)
    ):
        raise PermissionDenied(
            "Only an administrator or the assigned faculty can modify attendance records."
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
def calculate_attendance_percentages(*, student):
    """
    Calculate recorded attendance percentages for each class section.

    Only stored attendance records count toward the denominator.
    Sections without recorded attendance have percentage=None.
    """
    counts_by_section = {
        row["session__class_section_id"]: row
        for row in (
            AttendanceRecord.objects.filter(student=student)
            .values("session__class_section_id")
            .annotate(
                total_sessions=Count("pk"),
                attended_sessions=Count(
                    "pk",
                    filter=Q(
                        status=AttendanceRecord.Status.PRESENT
                    ),
                ),
            )
        )
    }

    sections = (
        ClassSection.objects.filter(
            Q(enrollments__student=student)
            | Q(
                attendance_sessions__attendance_records__student=student
            )
        )
        .select_related("course")
        .distinct()
        .order_by(
            "course__course_code",
            "section",
            "academic_term",
        )
    )

    summaries = []

    for section in sections:
        counts = counts_by_section.get(section.pk, {})
        total = counts.get("total_sessions", 0)
        attended = counts.get("attended_sessions", 0)

        percentage = (
            round(attended * 100 / total, 2)
            if total
            else None
        )

        summaries.append({
            "class_section": section,
            "total_sessions": total,
            "attended_sessions": attended,
            "percentage": percentage,
        })

    return summaries
