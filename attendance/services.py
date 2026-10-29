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
from .permissions import can_faculty_manage_section


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


def generate_attendance_report(
    user,
    *,
    class_section_id=None,
    date_from=None,
    date_to=None,
    student_usn=None,
):
    """
    Generate attendance report data aggregated from persistent attendance records.

    Traceability:
    - REQ-12: The system shall allow authorized users to generate attendance reports.
    - BR-08: Only authorized users shall be allowed to generate attendance reports
             containing student attendance information.

    Specification & Calculation Notes:
    - Denominator: 'Total Classes' represents the count of stored AttendanceRecord
      entries for each student in the relevant class section, matching BR-07, REQ-11,
      and the SRS glossary definition ("Percentage of attended sessions out of the
      total recorded sessions").
    - Numerator: 'Attended Classes' counts stored records with status PRESENT.
    - 'Absent Classes' counts stored records with status ABSENT.
    - 'Course ID' maps to Course.course_code (alphanumeric, unique).
    - Status Threshold: SRS Appendix B (Report Requirements) and Test Plan v1.1 do
      not specify an institutional threshold (such as 75%) or status labels such as
      'Eligible' / 'Low Attendance'. To avoid inventing an unapproved business rule,
      no percentage threshold is hardcoded. Active enrolled students with zero recorded
      sessions have percentage=None and status="No Records". Students with recorded
      attendance have status=None (rendered as '—' in the UI), leaving any eligibility
      classification to documented institutional policy.
    - Date Filtering Semantics: When a date range is applied, the report reflects
      attendance recorded within that period. Students without records in that period
      are not labeled "No Records", as that designation denotes students with zero
      attendance records across the class section.
    """
    if not user or not getattr(user, "is_authenticated", False):
        raise PermissionDenied(
            "Authentication is required to generate attendance reports."
        )

    user_role = getattr(user, "role", None)
    if user_role not in ("ADMIN", "FACULTY"):
        raise PermissionDenied(
            "Only administrators and faculty can generate attendance reports."
        )

    # 1. Determine permitted class sections scope based on role
    if user_role == "ADMIN":
        scope_sections = ClassSection.objects.all()
    elif user_role == "FACULTY":
        if hasattr(user, "faculty_profile") and user.faculty_profile:
            scope_sections = user.faculty_profile.class_sections.all()
        else:
            scope_sections = ClassSection.objects.none()
    else:
        raise PermissionDenied("Unauthorized user role.")

    # 2. Restrict to specific class section if requested
    if class_section_id is not None:
        try:
            target_section = ClassSection.objects.select_related(
                "course", "faculty"
            ).get(pk=class_section_id)
        except (ClassSection.DoesNotExist, ValueError):
            raise ValidationError("Selected class section does not exist.")

        if user_role == "FACULTY" and not can_faculty_manage_section(
            user, target_section
        ):
            raise PermissionDenied(
                "Faculty can only generate reports for their assigned class sections."
            )

        sections_qs = ClassSection.objects.filter(pk=target_section.pk)
    else:
        sections_qs = scope_sections

    # 3. Validate date range criteria
    if date_from and date_to and date_from > date_to:
        raise ValidationError("Start date cannot be after end date.")

    # If no sections exist within the allowed scope, report is empty
    if not sections_qs.exists():
        return []

    # 4. Filter persistent attendance records
    records_qs = AttendanceRecord.objects.filter(
        session__class_section__in=sections_qs
    )

    if date_from:
        records_qs = records_qs.filter(session__session_date__gte=date_from)
    if date_to:
        records_qs = records_qs.filter(session__session_date__lte=date_to)
    if student_usn:
        records_qs = records_qs.filter(student__usn__iexact=student_usn.strip())

    results = []

    # 5. Multi-student aggregation query for stored records
    if records_qs.exists():
        aggregated = (
            records_qs.values(
                "session__class_section_id",
                "session__class_section__section",
                "session__class_section__academic_term",
                "session__class_section__course__course_code",
                "session__class_section__course__course_name",
                "student_id",
                "student__usn",
                "student__name",
            )
            .annotate(
                total_classes=Count("pk"),
                attended_classes=Count(
                    "pk",
                    filter=Q(status=AttendanceRecord.Status.PRESENT),
                ),
                absent_classes=Count(
                    "pk",
                    filter=Q(status=AttendanceRecord.Status.ABSENT),
                ),
            )
            .order_by(
                "session__class_section__course__course_code",
                "session__class_section__section",
                "student__usn",
            )
        )

        for row in aggregated:
            total = row["total_classes"]
            attended = row["attended_classes"]
            absent = row["absent_classes"]
            percentage = round(attended * 100.0 / total, 2) if total else None
            status = "No Records" if total == 0 else None

            results.append({
                "student_id": row["student__usn"],
                "usn": row["student__usn"],
                "student_name": row["student__name"],
                "student_pk": row["student_id"],
                "course_id": row["session__class_section__course__course_code"],
                "course_code": row["session__class_section__course__course_code"],
                "course_name": row["session__class_section__course__course_name"],
                "section": row["session__class_section__section"],
                "academic_term": row["session__class_section__academic_term"],
                "class_section_id": row["session__class_section_id"],
                "total_classes": total,
                "attended_classes": attended,
                "absent_classes": absent,
                "percentage": percentage,
                "status": status,
            })

    # 6. Include enrolled active students who have zero attendance records when
    # neither date nor student filters are applied.
    # When a class section is queried without date or student filters, enrolled active
    # students in that section with no recorded attendance appear with total=0,
    # attended=0, absent=0, percentage=None, and status="No Records".
    # Include enrolled students who have no records for their own section.
    if not date_from and not date_to and not student_usn:
        recorded_pairs = {
            (row["student_pk"], row["class_section_id"])
            for row in results
        }

        unrecorded_enrollments = (
            Enrollment.objects.filter(
                class_section__in=sections_qs,
                student__is_active=True,
            )
            .select_related("student", "class_section__course")
            .order_by(
                "class_section__course__course_code",
                "class_section__section",
                "student__usn",
            )
        )

        for enrollment in unrecorded_enrollments:
            pair = (
                enrollment.student_id,
                enrollment.class_section_id,
            )

            if pair in recorded_pairs:
                continue

            results.append({
                "student_id": enrollment.student.usn,
                "usn": enrollment.student.usn,
                "student_name": enrollment.student.name,
                "student_pk": enrollment.student.student_id,
                "course_id": enrollment.class_section.course.course_code,
                "course_code": enrollment.class_section.course.course_code,
                "course_name": enrollment.class_section.course.course_name,
                "section": enrollment.class_section.section,
                "academic_term": enrollment.class_section.academic_term,
                "class_section_id": enrollment.class_section_id,
                "total_classes": 0,
                "attended_classes": 0,
                "absent_classes": 0,
                "percentage": None,
                "status": "No Records",
            })

            recorded_pairs.add(pair)

        results.sort(
            key=lambda row: (
                row["course_id"],
                row["section"],
                row["student_id"],
            )
        )

    return results
