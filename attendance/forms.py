
from django import forms

from .models import Course, ClassSection, Faculty


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
