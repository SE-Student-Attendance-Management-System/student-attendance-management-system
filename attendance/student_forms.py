from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from .models import Student


class StudentForm(forms.ModelForm):
    """Validate student profile fields against SRS Appendix B."""

    class Meta:
        model = Student
        fields = ["usn", "name", "email", "phone", "program", "semester"]
        widgets = {
            "usn": forms.TextInput(attrs={"maxlength": 15, "autocomplete": "off"}),
            "name": forms.TextInput(attrs={"maxlength": 100}),
            "email": forms.EmailInput(attrs={"maxlength": 100}),
            "phone": forms.TextInput(attrs={"maxlength": 15, "inputmode": "tel"}),
            "program": forms.TextInput(attrs={"maxlength": 50}),
            "semester": forms.NumberInput(attrs={"min": 1, "max": 99}),
        }

    def clean_usn(self):
        usn = self.cleaned_data["usn"].strip()
        if not usn:
            raise forms.ValidationError("Student ID / USN is required.")
        if len(usn) > 15:
            raise forms.ValidationError("Student ID / USN must be at most 15 characters.")
        if not usn.isascii() or not usn.isalnum():
            raise forms.ValidationError(
                "Student ID / USN must contain only English letters and numbers."
            )

        duplicates = Student.objects.filter(usn__iexact=usn)
        if self.instance and self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("A student with this USN already exists.")
        return usn

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError("Student Name is required.")
        if len(name) > 100:
            raise forms.ValidationError("Student Name must be at most 100 characters.")
        return name

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if not email:
            raise forms.ValidationError("Email is required.")
        if len(email) > 100:
            raise forms.ValidationError("Email must be at most 100 characters.")
        try:
            validate_email(email)
        except ValidationError as exc:
            raise forms.ValidationError("Enter a valid email address.") from exc

        duplicates = Student.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("A student with this email already exists.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if not phone:
            return ""
        if len(phone) > 15:
            raise forms.ValidationError("Phone Number must be at most 15 characters.")
        # SRS permits Numeric/String; allow an optional leading + and common
        # visual separators while requiring the actual characters to be digits.
        normalized = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if normalized.startswith("+"):
            normalized = normalized[1:]
        if not normalized.isascii() or not normalized.isdigit():
            raise forms.ValidationError(
                "Enter a valid phone number using digits and optional +, spaces, hyphens or parentheses."
            )
        return phone

    def clean_program(self):
        program = self.cleaned_data["program"].strip()
        if not program:
            raise forms.ValidationError("Course/Program is required.")
        if len(program) > 50:
            raise forms.ValidationError("Course/Program must be at most 50 characters.")
        return program

    def clean_semester(self):
        semester = self.cleaned_data["semester"]
        if semester is None:
            raise forms.ValidationError("Semester is required.")
        if not 1 <= semester <= 99:
            raise forms.ValidationError("Semester must be between 1 and 99.")
        return semester
