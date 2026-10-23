
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CourseForm, ClassSectionForm
from .models import Course, ClassSection


def can_manage_courses(user):
    return user.is_authenticated and user.role == "ADMIN"


@login_required
@user_passes_test(can_manage_courses)
def course_list(request):
    courses = Course.objects.prefetch_related(
        "class_sections__faculty"
    ).order_by("course_code")

    return render(
        request,
        "attendance/course_list.html",
        {"courses": courses},
    )


@login_required
@user_passes_test(can_manage_courses)
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


@login_required
@user_passes_test(can_manage_courses)
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


@login_required
@user_passes_test(can_manage_courses)
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
