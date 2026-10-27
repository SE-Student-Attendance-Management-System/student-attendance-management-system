from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render

from .student_forms import StudentForm, StudentSearchForm
from .models import Student
from .permissions import admin_required, faculty_required


@admin_required
def student_list(request):
    """List student records for the administrator's management workflow."""
    students = Student.objects.order_by("usn")
    return render(request, "attendance/student_list.html", {"students": students})


@admin_required
def student_create(request):
    """Create a student record; only administrators may manage profiles."""
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
            except IntegrityError:
                form.add_error(None, "A student with this USN or email already exists.")
            else:
                messages.success(request, "Student record created successfully.")
                return redirect("student_list")
    else:
        form = StudentForm()

    return render(
        request,
        "attendance/student_form.html",
        {"form": form, "page_title": "Add Student", "submit_label": "Create student"},
    )


@admin_required
def student_update(request, pk):
    """Update a student record without changing its linked login relationship."""
    student = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
            except IntegrityError:
                form.add_error(None, "A student with this USN or email already exists.")
            else:
                messages.success(request, "Student record updated successfully.")
                return redirect("student_list")
    else:
        form = StudentForm(instance=student)

    return render(
        request,
        "attendance/student_form.html",
        {"form": form, "student": student, "page_title": "Update Student", "submit_label": "Save changes"},
    )


@faculty_required
def student_search(request):
    """Search by exact USN or student name and handle validation/no-match states."""
    submitted = "query" in request.GET or "search_by" in request.GET
    form = StudentSearchForm(request.GET if submitted else None)
    results = Student.objects.none()
    not_found = False

    if submitted and form.is_valid():
        search_by = form.cleaned_data["search_by"]
        query = form.cleaned_data["query"]
        if search_by == "usn":
            results = Student.objects.filter(usn__iexact=query).order_by("usn")
        else:
            results = Student.objects.filter(name__icontains=query).order_by("name", "usn")
        not_found = not results.exists()

    return render(
        request,
        "attendance/student_search.html",
        {
            "form": form,
            "results": results,
            "submitted": submitted,
            "not_found": not_found,
        },
    )


@faculty_required
def student_detail(request, pk):
    """Display the stored profile for one student to an authorized Admin/Faculty user."""
    student = get_object_or_404(Student, pk=pk)
    return render(request, "attendance/student_detail.html", {"student": student})
