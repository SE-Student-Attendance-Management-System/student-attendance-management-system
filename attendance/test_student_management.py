from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Student
from .student_forms import StudentForm

User = get_user_model()


class StudentFormTests(TestCase):
    def setUp(self):
        self.valid_data = {
            "usn": "USN000001",
            "name": "Alice Example",
            "email": "alice@example.test",
            "phone": "9876500001",
            "program": "CSE",
            "semester": 3,
        }

    def test_valid_student_data_is_accepted(self):
        form = StudentForm(data=self.valid_data)
        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_optional_phone_can_be_blank(self):
        form = StudentForm(data={**self.valid_data, "phone": ""})
        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_usn_must_be_alphanumeric_and_at_most_15_characters(self):
        for value in ("USN-00001", "USN00000000000001", "USN 01", "ÜSN123"):
            with self.subTest(usn=value):
                form = StudentForm(data={**self.valid_data, "usn": value})
                self.assertFalse(form.is_valid())
                self.assertIn("usn", form.errors)

    def test_maximum_valid_usn_length_is_accepted(self):
        form = StudentForm(data={**self.valid_data, "usn": "A12345678901234"})
        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_maximum_valid_lengths_for_other_fields_are_accepted(self):
        maximum_data = {
            **self.valid_data,
            "name": "N" * 100,
            "email": f"{'a' * 64}@{'d' * 22}.example.test",
            "phone": "1" * 15,
            "program": "P" * 50,
        }
        self.assertEqual(len(maximum_data["email"]), 100)
        form = StudentForm(data=maximum_data)
        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_required_fields_cannot_be_blank(self):
        for field in ("usn", "name", "email", "program", "semester"):
            with self.subTest(field=field):
                form = StudentForm(data={**self.valid_data, field: ""})
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_name_email_and_program_length_limits(self):
        cases = [
            ("name", "N" * 101),
            ("email", "a" * 90 + "@example.test"),
            ("program", "P" * 51),
        ]
        for field, value in cases:
            with self.subTest(field=field):
                form = StudentForm(data={**self.valid_data, field: value})
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_malformed_email_and_phone_are_rejected(self):
        for field, value in (("email", "not-an-email"), ("phone", "123ABC"), ("phone", "1" * 16)):
            with self.subTest(field=field, value=value):
                form = StudentForm(data={**self.valid_data, field: value})
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_duplicate_usn_and_email_are_rejected(self):
        Student.objects.create(
            usn="USN000001", name="Existing Student", email="existing@example.test",
            program="CSE", semester=3,
        )
        form = StudentForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn("usn", form.errors)

        form = StudentForm(data={**self.valid_data, "usn": "USN000002", "email": "existing@example.test"})
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_semester_must_be_in_model_supported_range(self):
        for semester in (0, 100, "abc"):
            with self.subTest(semester=semester):
                form = StudentForm(data={**self.valid_data, "semester": semester})
                self.assertFalse(form.is_valid())
                self.assertIn("semester", form.errors)


class StudentManagementViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="student_admin", password="test-password-123", role=User.Role.ADMIN)
        self.faculty = User.objects.create_user(username="student_faculty", password="test-password-123", role=User.Role.FACULTY)
        self.student_user = User.objects.create_user(username="student_user", password="test-password-123", role=User.Role.STUDENT)
        self.student = Student.objects.create(
            usn="USN100001", name="Existing Student", email="existing@example.test",
            program="CSE", semester=3,
        )

    def valid_payload(self, **overrides):
        data = {
            "usn": "USN100002", "name": "New Student", "email": "new@example.test",
            "phone": "", "program": "CSE", "semester": 4,
        }
        data.update(overrides)
        return data

    def test_admin_can_create_student_record(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("student_create"), self.valid_payload())
        self.assertRedirects(response, reverse("student_list"))
        self.assertTrue(Student.objects.filter(usn="USN100002", name="New Student").exists())

    def test_admin_can_update_student_record(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("student_update", kwargs={"pk": self.student.pk}),
            self.valid_payload(
                usn=self.student.usn, email=self.student.email,
                name="Updated Student", phone="9876501234",
            ),
        )
        self.assertRedirects(response, reverse("student_list"))
        self.student.refresh_from_db()
        self.assertEqual(self.student.name, "Updated Student")
        self.assertEqual(self.student.phone, "9876501234")

    def test_invalid_update_does_not_modify_existing_record(self):
        self.student.__class__.objects.create(
            usn="USN100003",
            name="Other Student",
            email="other@example.test",
            program="CSE",
            semester=2,
        )
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("student_update", kwargs={"pk": self.student.pk}),
            self.valid_payload(
                usn="USN100003",
                email="updated@example.test",
                name="Must Not Persist",
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("usn", response.context["form"].errors)
        self.student.refresh_from_db()
        self.assertEqual(self.student.usn, "USN100001")
        self.assertEqual(self.student.name, "Existing Student")
        self.assertEqual(self.student.email, "existing@example.test")

    def test_invalid_submission_does_not_create_partial_record(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("student_create"), self.valid_payload(usn="bad-usn"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Student.objects.filter(usn="bad-usn").exists())

    def test_only_admin_can_create_or_update_students(self):
        for user in (None, self.faculty, self.student_user):
            with self.subTest(user=getattr(user, "username", "anonymous")):
                self.client.logout()
                if user:
                    self.client.force_login(user)
                get_response = self.client.get(reverse("student_create"))
                if user is None:
                    self.assertEqual(get_response.status_code, 302)
                else:
                    self.assertEqual(get_response.status_code, 403)
                post_response = self.client.post(reverse("student_create"), self.valid_payload(usn="USN999999"))
                if user is None:
                    self.assertEqual(post_response.status_code, 302)
                else:
                    self.assertEqual(post_response.status_code, 403)
                self.assertFalse(Student.objects.filter(usn="USN999999").exists())

                update_url = reverse("student_update", kwargs={"pk": self.student.pk})
                update_get_response = self.client.get(update_url)
                update_post_response = self.client.post(
                    update_url,
                    self.valid_payload(
                        usn=self.student.usn,
                        email=self.student.email,
                        name="Unauthorized update",
                    ),
                )
                expected_status = 302 if user is None else 403
                self.assertEqual(update_get_response.status_code, expected_status)
                self.assertEqual(update_post_response.status_code, expected_status)
                self.student.refresh_from_db()
                self.assertEqual(self.student.name, "Existing Student")

    def test_update_missing_student_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("student_update", kwargs={"pk": 999999}))
        self.assertEqual(response.status_code, 404)
