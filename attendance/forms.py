
from django import forms
from django.core.exceptions import PermissionDenied

from .models import Course, ClassSection, Faculty
from .permissions import can_faculty_manage_section


class CourseForm(forms.ModelForm):
    """Validate course details."""

    class Meta:
        model = Course
        fields = ["course_code", "course_name", "semester"]
        widgets = {
            "course_code": forms.TextInput(
                attrs={"placeholder": "e.g. CS101"}
            ),
            "course_name": forms.TextInput(
                attrs={"placeholder": "e.g. Database Management Systems"}
            ),
            "semester": forms.NumberInput(
                attrs={"min": 1, "max": 99}
            ),
        }

    def clean_course_code(self):
        course_code = self.cleaned_data["course_code"].strip()

        if not course_code.isascii() or not course_code.isalnum():
            raise forms.ValidationError(
                "Course ID must contain only English letters and numbers."
            )

        return course_code

    def clean_course_name(self):
        course_name = self.cleaned_data["course_name"].strip()

        if not course_name:
            raise forms.ValidationError("Course Name is required.")

        return course_name


class ClassSectionForm(forms.ModelForm):
    """Validate faculty, section, and academic term."""

    class Meta:
        model = ClassSection
        fields = ["faculty", "section", "academic_term"]
        widgets = {
            "section": forms.TextInput(
                attrs={"placeholder": "e.g. A"}
            ),
            "academic_term": forms.TextInput(
                attrs={"placeholder": "e.g. 2026-27"}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.course = kwargs.pop("course", None)
        super().__init__(*args, **kwargs)

        self.fields["faculty"].queryset = Faculty.objects.filter(
            is_active=True
        )

    def clean_section(self):
        section = self.cleaned_data["section"].strip()

        if not section:
            raise forms.ValidationError(
                "Class/Section is required."
            )

        return section

    def clean_academic_term(self):
        academic_term = self.cleaned_data["academic_term"].strip()

        if not academic_term:
            raise forms.ValidationError(
                "Academic term is required."
            )

        return academic_term

    def clean(self):
        cleaned_data = super().clean()

        section = cleaned_data.get("section")
        academic_term = cleaned_data.get("academic_term")

        course = self.course
        if course is None and self.instance and self.instance.pk:
            course = self.instance.course

        if course and section and academic_term:
            duplicates = ClassSection.objects.filter(
                course=course,
                section=section,
                academic_term=academic_term,
            )

            if self.instance and self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)

            if duplicates.exists():
                raise forms.ValidationError(
                    "This section already exists for this course and academic term."
                )

        return cleaned_data


class AttendanceReportForm(forms.Form):
    """Filter form for generating attendance reports (REQ-12, BR-08)."""

    class_section = forms.ModelChoiceField(
        queryset=ClassSection.objects.none(),
        required=False,
        empty_label="All Class Sections",
        label="Class Section",
        widget=forms.Select(attrs={"class": "form-control", "id": "id_class_section"}),
        error_messages={"invalid_choice": "Selected class section does not exist."},
    )
    date_from = forms.DateField(
        required=False,
        label="From Date",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
                "placeholder": "YYYY-MM-DD",
                "id": "id_date_from",
            }
        ),
    )
    date_to = forms.DateField(
        required=False,
        label="To Date",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
                "placeholder": "YYYY-MM-DD",
                "id": "id_date_to",
            }
        ),
    )
    student_id = forms.CharField(
        required=False,
        max_length=15,
        label="Student ID / USN",
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. USN001",
                "autocomplete": "off",
                "id": "id_student_id",
            }
        ),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if user and getattr(user, "is_authenticated", False):
            if user.role == "ADMIN":
                self.fields["class_section"].queryset = (
                    ClassSection.objects.select_related("course", "faculty")
                    .order_by("course__course_code", "section", "academic_term")
                )
                self.fields["class_section"].empty_label = "All Class Sections"
            elif user.role == "FACULTY":
                if hasattr(user, "faculty_profile") and user.faculty_profile:
                    self.fields["class_section"].queryset = (
                        user.faculty_profile.class_sections.select_related("course")
                        .order_by("course__course_code", "section", "academic_term")
                    )
                else:
                    self.fields["class_section"].queryset = ClassSection.objects.none()
                self.fields["class_section"].empty_label = "All Assigned Class Sections"
            else:
                self.fields["class_section"].queryset = ClassSection.objects.none()

    def clean_student_id(self):
        student_id = self.cleaned_data.get("student_id", "").strip()
        if not student_id:
            return ""
        if len(student_id) > 15:
            raise forms.ValidationError("Student ID / USN must be at most 15 characters.")
        if not student_id.isascii() or not student_id.isalnum():
            raise forms.ValidationError(
                "Student ID / USN must contain only English letters and numbers."
            )
        return student_id

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")
        class_section = cleaned_data.get("class_section")

        if date_from and date_to and date_from > date_to:
            self.add_error("date_from", "Start date cannot be after end date.")

        if self.user and self.user.role == "FACULTY" and class_section:
            if not can_faculty_manage_section(self.user, class_section):
                raise PermissionDenied(
                    "Faculty can only generate reports for their assigned class sections."
                )

        return cleaned_data
