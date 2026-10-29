from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.views.decorators.http import require_GET
from .models import (
    AttendanceRecord,
    AttendanceSession,
    Enrollment,
    Student,
)
from .permissions import can_faculty_manage_section
from .services import (
    calculate_attendance_percentages,
    generate_attendance_report,
    mark_attendance,
    update_attendance,
)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CourseForm, ClassSectionForm, AttendanceReportForm
from .models import Course, ClassSection
from .permissions import admin_required, can_manage_courses


# ==============================================================================
# Authentication & Landing Views (Issue #11 / Issue #12)
# ==============================================================================

@login_required
def home(request):
    """
    Authenticated landing and role-based dashboard view (Issue #11 & Issue #12).
    Displays the authenticated user's details, role status, and permitted operations
    according to their role (Administrator, Faculty, Student).
    """
    user = request.user
    context = {
        "user": user,
        "is_admin": user.role == "ADMIN",
        "is_faculty": user.role == "FACULTY",
        "is_student": user.role == "STUDENT",
    }

    if user.role == "FACULTY" and hasattr(user, "faculty_profile") and user.faculty_profile:
        context["faculty_sections"] = (
            user.faculty_profile.class_sections.select_related("course").order_by(
                "course__course_code"
            )
        )
    elif user.role == "STUDENT" and hasattr(user, "student_profile") and user.student_profile:
        context["student_enrollments"] = (
            user.student_profile.enrollments.select_related(
                "class_section__course", "class_section__faculty"
            ).order_by("class_section__course__course_code")
        )

    return render(request, "home.html", context)


# ==============================================================================
# Course Management Views (Issue #20 / PR #26 / Issue #12)
# ==============================================================================

@admin_required
def course_list(request):
    courses = Course.objects.prefetch_related(
        "class_sections__faculty"
    ).order_by("course_code")

    return render(
        request,
        "attendance/course_list.html",
        {"courses": courses},
    )


@admin_required
@transaction.atomic
def course_create(request):
    if request.method == "POST":
        course_form = CourseForm(request.POST)
        section_form = ClassSectionForm(request.POST)

        # Validate both forms before saving either object.
        if course_form.is_valid() and section_form.is_valid():
            course = course_form.save()

            section = section_form.save(commit=False)
            section.course = course
            section.save()

            messages.success(request, "Course created successfully.")
            return redirect("course_list")
    else:
        course_form = CourseForm()
        section_form = ClassSectionForm()

    return render(
        request,
        "attendance/course_form.html",
        {
            "course_form": course_form,
            "section_form": section_form,
            "page_title": "Create Course",
        },
    )


@admin_required
@transaction.atomic
def course_update(request, pk):
    """Edit course details and its section when there is only one."""
    course = get_object_or_404(Course, pk=pk)
    sections = course.class_sections.order_by("pk")

    # A course with multiple sections must use the section-specific URL.
    if sections.count() > 1:
        messages.error(
            request,
            "This course has multiple sections. Use the section-specific Edit link.",
        )
        return redirect("course_list")

    section = sections.first()

    if request.method == "POST":
        course_form = CourseForm(request.POST, instance=course)
        section_form = ClassSectionForm(
            request.POST,
            instance=section,
            course=course,
        )

        if course_form.is_valid() and section_form.is_valid():
            course_form.save()

            section = section_form.save(commit=False)
            section.course = course
            section.save()

            messages.success(request, "Course updated successfully.")
            return redirect("course_list")
    else:
        course_form = CourseForm(instance=course)
        section_form = ClassSectionForm(
            instance=section,
            course=course,
        )

    return render(
        request,
        "attendance/course_form.html",
        {
            "course_form": course_form,
            "section_form": section_form,
            "page_title": "Update Course",
        },
    )


@admin_required
@transaction.atomic
def section_update(request, pk, section_pk):
    """Edit a course and the specific section selected by the user."""
    course = get_object_or_404(Course, pk=pk)
    section = get_object_or_404(
        ClassSection,
        pk=section_pk,
        course=course,
    )

    if request.method == "POST":
        course_form = CourseForm(request.POST, instance=course)
        section_form = ClassSectionForm(
            request.POST,
            instance=section,
            course=course,
        )

        if course_form.is_valid() and section_form.is_valid():
            course_form.save()
            section_form.save()

            messages.success(
                request,
                "Course and section updated successfully.",
            )
            return redirect("course_list")
    else:
        course_form = CourseForm(instance=course)
        section_form = ClassSectionForm(
            instance=section,
            course=course,
        )

    return render(
        request,
        "attendance/course_form.html",
        {
            "course_form": course_form,
            "section_form": section_form,
            "page_title": "Update Course and Section",
        },
    )

# ==============================================================================
# Attendance Management Views (Issue #31)
# ==============================================================================

@login_required
@require_GET
def student_attendance_history(request):
    """Display attendance records belonging only to the logged-in student."""
    if request.user.role != "STUDENT":
        raise PermissionDenied(
            "Only students can access their attendance history."
        )

    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        raise PermissionDenied(
            "Your account is not linked to a student profile."
        )

    records = (
        AttendanceRecord.objects.filter(student=student)
        .select_related(
            "session__class_section__course",
            "session__class_section__faculty",
        )
        .order_by("-session__session_date", "-session__session_no")
    )

    return render(
        request,
        "attendance/student_attendance_history.html",
        {
	    "student": student,
	    "records": records,
	    "attendance_summaries": (
	        calculate_attendance_percentages(student=student)
	    ),
	},
    )


@login_required
def attendance_sessions(request):
    """List attendance sessions the current user is allowed to manage."""
    if request.user.role == "ADMIN":
        sessions = AttendanceSession.objects.select_related(
            "class_section__course",
            "class_section__faculty",
        ).order_by("-session_date", "session_no")
    elif request.user.role == "FACULTY":
        sessions = AttendanceSession.objects.filter(
            class_section__faculty__user=request.user,
        ).select_related(
            "class_section__course",
            "class_section__faculty",
        ).order_by("-session_date", "session_no")
    else:
        raise PermissionDenied(
            "Only administrators and faculty can manage attendance."
        )

    return render(
        request,
        "attendance/attendance_sessions.html",
        {"sessions": sessions},
    )


@login_required
def attendance_session_create(request, section_pk):
    """Create a session for a class section managed by the current user."""
    from django.utils import timezone

    from .models import ClassSection

    section = get_object_or_404(ClassSection, pk=section_pk)

    if not can_faculty_manage_section(request.user, section):
        raise PermissionDenied(
            "You cannot create attendance sessions for this class."
        )

    if request.method == "POST":
        session_date = request.POST.get("session_date", "").strip()
        session_no = request.POST.get("session_no", "1").strip()

        try:
            from datetime import date

            parsed_date = date.fromisoformat(session_date)
            parsed_session_no = int(session_no)

            if parsed_session_no < 1 or parsed_session_no > 32767:
                raise ValueError

            if parsed_date > timezone.localdate():
                messages.error(
                    request,
                    "Attendance sessions cannot be created for a future date.",
                )
            else:
                session, created = AttendanceSession.objects.get_or_create(
                    class_section=section,
                    session_date=parsed_date,
                    session_no=parsed_session_no,
                )

                if created:
                    messages.success(
                        request, "Attendance session created successfully."
                    )
                else:
                    messages.info(
                        request, "That attendance session already exists."
                    )

                return redirect(
                    "attendance_mark",
                    session_pk=session.session_id,
                )

        except (ValueError, TypeError):
            messages.error(
                request,
                "Enter a valid date and a session number greater than zero.",
            )

    return render(
        request,
        "attendance/attendance_session_form.html",
        {
            "section": section,
            "today": timezone.localdate().isoformat(),
        },
    )


@login_required
def attendance_mark(request, session_pk):
    """Display enrolled students and mark attendance without duplicate records."""
    session = get_object_or_404(
        AttendanceSession.objects.select_related(
            "class_section__course",
            "class_section__faculty",
        ),
        session_id=session_pk,
    )

    if not can_faculty_manage_section(request.user, session.class_section):
        raise PermissionDenied(
            "You cannot manage attendance for this class."
        )

    enrollments = Enrollment.objects.filter(
        class_section=session.class_section,
        student__is_active=True,
    ).select_related("student").order_by("student__usn")

    if request.method == "POST":
        marked_count = 0
        duplicate_count = 0

        for enrollment in enrollments:
            student = enrollment.student
            status = request.POST.get(
                f"status_{student.student_id}", ""
            ).strip()

            # An omitted field is not a valid attendance submission.
            if status not in AttendanceRecord.Status.values:
                messages.error(
                    request,
                    f"Select Present or Absent for {student.usn}.",
                )
                continue

            existing = AttendanceRecord.objects.filter(
                session=session,
                student=student,
            ).first()

            if existing:
                # Repeated submissions do not create duplicate records.
                duplicate_count += 1
                continue

            try:
                # A savepoint keeps a duplicate-key race from breaking
                # the surrounding request transaction.
                with transaction.atomic():
                    mark_attendance(
                        session_id=session.session_id,
                        student_id=student.student_id,
                        status=status,
                        marked_by=request.user,
                    )
                marked_count += 1

            except IntegrityError:
                duplicate_count += 1

            except ValidationError as exc:
                messages.error(request, str(exc))

        if marked_count:
            messages.success(
                request,
                f"Marked attendance for {marked_count} student(s).",
            )

        if duplicate_count:
            messages.info(
                request,
                f"Skipped {duplicate_count} student(s) who already have "
                "attendance records. Use Edit to change existing records.",
            )

        return redirect("attendance_mark", session_pk=session.session_id)

        records = AttendanceRecord.objects.filter(
        session=session,
    ).select_related("student").order_by("student__usn")
    records = AttendanceRecord.objects.filter(
    session=session,
).select_related("student").order_by("student__usn")
    recorded_student_ids = set(
        records.values_list("student_id", flat=True)
    )

    unmarked_students = [
        enrollment.student
        for enrollment in enrollments
        if enrollment.student_id not in recorded_student_ids
    ]

    return render(
        request,
        "attendance/attendance_mark.html",
        {
            "session": session,
            "attendance_records": records,
            "unmarked_students": unmarked_students,
            "status_choices": AttendanceRecord.Status.choices,
        },
    )


@login_required
def attendance_update(request, attendance_pk):
    """Modify an existing record using the audited attendance service."""
    record = get_object_or_404(
        AttendanceRecord.objects.select_related(
            "session__class_section__course",
            "session__class_section__faculty",
            "student",
        ),
        attendance_id=attendance_pk,
    )

    if not can_faculty_manage_section(
        request.user, record.session.class_section
    ):
        raise PermissionDenied(
            "You cannot modify attendance for this class."
        )

    if request.method == "POST":
        status = request.POST.get("status", "").strip()

        if status not in AttendanceRecord.Status.values:
            messages.error(request, "Select a valid attendance status.")
        else:
            try:
                update_attendance(
                    attendance_id=record.attendance_id,
                    status=status,
                    changed_by=request.user,
                )
                messages.success(
                    request,
                    f"Attendance updated for {record.student.usn}.",
                )
                return redirect(
                    "attendance_mark",
                    session_pk=record.session.session_id,
                )
            except ValidationError as exc:
                messages.error(request, str(exc))

    return render(
        request,
        "attendance/attendance_update.html",
        {
            "record": record,
            "status_choices": AttendanceRecord.Status.choices,
        },
    )


# ==============================================================================
# Attendance Report Generation Views (Issue #34 / REQ-12 / BR-08)
# ==============================================================================

@login_required
def attendance_report(request):
    """
    Generate attendance reports for authorized administrators and faculty (Issue #34).

    Traceability:
    - Functional Requirement: REQ-12 (Generate attendance reports)
    - Business Rule: BR-08 (Only authorized users shall generate attendance reports)
    - Performance Requirement: Reports shall complete within 5 seconds for normal-sized datasets
    """
    if request.user.role not in ("ADMIN", "FACULTY"):
        raise PermissionDenied("Students cannot access report generation.")

    # Server-side validation and authorization check on class_section criteria
    raw_section_id = (
        request.GET.get("class_section")
        or request.POST.get("class_section")
        or ""
    ).strip()

    invalid_section_error = None
    if raw_section_id:
        try:
            section_pk = int(raw_section_id)
            target_sec = ClassSection.objects.select_related("faculty").get(
                pk=section_pk
            )
            if request.user.role == "FACULTY" and not can_faculty_manage_section(
                request.user, target_sec
            ):
                raise PermissionDenied(
                    "Faculty can only generate reports for their assigned class sections."
                )
        except ValueError:
            invalid_section_error = "Select a valid class section."
        except ClassSection.DoesNotExist:
            invalid_section_error = "Selected class section does not exist."

    submitted = (
        "generate" in request.GET
        or "class_section" in request.GET
        or "course" in request.GET
        or "date_from" in request.GET
        or "date_to" in request.GET
        or "student_id" in request.GET
        or "student_usn" in request.GET
        or request.method == "POST"
    )

    data_source = (
        request.POST
        if request.method == "POST"
        else (request.GET if submitted else None)
    )
    form = AttendanceReportForm(data_source, user=request.user)

    # Use a specific message for malformed, non-numeric section IDs.
    # Numeric IDs that do not exist retain the form's configured message.
    if invalid_section_error == "Select a valid class section.":
        form.fields["class_section"].error_messages["invalid_choice"] = (
            "Select a valid class section."
        )
    report_rows = []
    selected_section = None

    # Run form validation first; subsequent custom errors must not be
    # cleared by Django's full_clean() process.
    form_is_valid = form.is_valid() if submitted else False

    if invalid_section_error:
        form.add_error("class_section", invalid_section_error)

    if submitted and form_is_valid and not invalid_section_error:
        selected_section = form.cleaned_data.get("class_section")
        selected_course = form.cleaned_data.get("course")
        date_from = form.cleaned_data.get("date_from")
        date_to = form.cleaned_data.get("date_to")
        student_id = form.cleaned_data.get("student_id") or request.GET.get("student_usn", "").strip()

        try:
            report_rows = generate_attendance_report(
                user=request.user,
                class_section_id=selected_section.pk if selected_section else None,
                course_id=selected_course.pk if selected_course else None,
                date_from=date_from,
                date_to=date_to,
                student_usn=student_id,
            )
        except ValidationError as exc:
            form.add_error(None, exc.message if hasattr(exc, "message") else str(exc))

    context = {
        "form": form,
        "report_rows": report_rows,
        "submitted": submitted,
        "selected_section": selected_section,
        "has_data": bool(report_rows),
        "total_records": len(report_rows),
    }

    return render(request, "attendance/attendance_report.html", context)
