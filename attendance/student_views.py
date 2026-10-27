from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render

from .student_forms import StudentForm
from .models import Student
from .permissions import admin_required


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
