from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Student

User = get_user_model()


class StudentSearchAndDetailTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="search_admin", password="test-password-123", role=User.Role.ADMIN
        )
        self.faculty = User.objects.create_user(
            username="search_faculty", password="test-password-123", role=User.Role.FACULTY
        )
        self.student_user = User.objects.create_user(
            username="search_student", password="test-password-123", role=User.Role.STUDENT
        )
        self.student = Student.objects.create(
            usn="USN150001",
            name="John Smith",
            email="john.search@example.test",
            phone="9876501234",
            program="CSE",
            semester=5,
        )
        self.same_name_student = Student.objects.create(
            usn="USN150002",
            name="John Smith",
            email="john.second@example.test",
            program="ECE",
            semester=3,
        )
        self.other_student = Student.objects.create(
            usn="USN150003",
            name="Alice Example",
            email="alice.search@example.test",
            program="CSE",
            semester=2,
        )
        self.search_url = reverse("student_search")
        self.detail_url = reverse("student_detail", kwargs={"pk": self.student.pk})

    def search(self, query, search_by="usn"):
        return self.client.get(self.search_url, {"search_by": search_by, "query": query})

    def test_admin_can_search_exact_usn_and_view_correct_stored_result(self):
        self.client.force_login(self.admin)
        response = self.search(self.student.usn)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["results"]), [self.student])
        for value in (self.student.usn, self.student.name, self.student.email,
                      self.student.program, str(self.student.semester)):
            self.assertContains(response, value)
        self.assertContains(response, reverse("student_detail", kwargs={"pk": self.student.pk}))
        self.assertNotContains(response, self.same_name_student.email)

    def test_usn_search_ignores_case_and_surrounding_whitespace(self):
        self.client.force_login(self.admin)
        response = self.search(f"  {self.student.usn.lower()}  ")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([s.pk for s in response.context["results"]], [self.student.pk])

    def test_name_search_returns_all_case_insensitive_matches(self):
        self.client.force_login(self.admin)
        response = self.search("john smith", search_by="name")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {s.pk for s in response.context["results"]},
            {self.student.pk, self.same_name_student.pk},
        )
        self.assertContains(response, "Matching students (2)")

    def test_blank_search_is_reported_as_validation_error(self):
        self.client.force_login(self.admin)
        response = self.search("")

        self.assertEqual(response.status_code, 200)
        self.assertIn("query", response.context["form"].errors)
        self.assertContains(response, "Enter a Student ID / USN or Student Name to search.")
        self.assertEqual(len(response.context["results"]), 0)

    def test_invalid_usn_format_is_rejected(self):
        self.client.force_login(self.admin)
        response = self.search("USN-150001")

        self.assertEqual(response.status_code, 200)
        self.assertIn("query", response.context["form"].errors)
        self.assertContains(response, "only English letters and numbers")
        self.assertEqual(len(response.context["results"]), 0)

    def test_overlength_usn_is_rejected(self):
        self.client.force_login(self.admin)
        response = self.search("U" * 16)

        self.assertEqual(response.status_code, 200)
        self.assertIn("query", response.context["form"].errors)
        self.assertEqual(len(response.context["results"]), 0)

    def test_nonexistent_usn_shows_clear_not_found_message(self):
        self.client.force_login(self.admin)
        response = self.search("INVALID99")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["not_found"])
        self.assertContains(response, "No student records matched")

    def test_partial_usn_does_not_return_a_record(self):
        self.client.force_login(self.admin)
        response = self.search("USN15000")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["not_found"])
        self.assertEqual(len(response.context["results"]), 0)

    def test_detail_page_displays_stored_fields_and_optional_phone_state(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["student"], self.student)
        for value in (self.student.usn, self.student.name, self.student.email,
                      self.student.phone, self.student.program, str(self.student.semester)):
            self.assertContains(response, value)
        optional_phone_student = self.same_name_student
        response = self.client.get(reverse("student_detail", kwargs={"pk": optional_phone_student.pk}))
        self.assertContains(response, "Not provided")

    def test_detail_page_renders_maximum_length_profile_fields(self):
        long_name = "N" * 100
        long_usn = "A12345678901234"
        long_program = "P" * 50
        long_phone = "1" * 15
        long_email = f"{'a' * 64}@{'d' * 22}.example.test"
        self.assertEqual(len(long_email), 100)
        maximum_student = Student.objects.create(
            usn=long_usn,
            name=long_name,
            email=long_email,
            phone=long_phone,
            program=long_program,
            semester=99,
        )
        self.client.force_login(self.admin)
        response = self.client.get(reverse("student_detail", kwargs={"pk": maximum_student.pk}))
        self.assertEqual(response.status_code, 200)
        for value in (long_usn, long_name, long_email, long_phone, long_program, "99"):
            self.assertContains(response, value)

    def test_detail_page_for_missing_student_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("student_detail", kwargs={"pk": 999999}))
        self.assertEqual(response.status_code, 404)

    def test_student_list_links_to_search_and_detail(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("student_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("student_search"))
        self.assertContains(response, reverse("student_detail", kwargs={"pk": self.student.pk}))

    def test_admin_and_faculty_can_search_and_view_profiles(self):
        for user in (self.admin, self.faculty):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                search_response = self.search(self.student.usn)
                self.assertEqual(search_response.status_code, 200)
                self.assertEqual(list(search_response.context["results"]), [self.student])
                detail_response = self.client.get(self.detail_url)
                self.assertEqual(detail_response.status_code, 200)

    def test_search_and_detail_are_not_accessible_to_anonymous_users(self):
        for url in (self.search_url, self.detail_url):
            with self.subTest(url=url):
                self.client.logout()
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)

    def test_student_role_cannot_search_or_view_other_student_profiles(self):
        for url in (self.search_url, self.detail_url):
            with self.subTest(url=url):
                self.client.force_login(self.student_user)
                response = self.client.get(url, {"search_by": "usn", "query": self.student.usn})
                self.assertEqual(response.status_code, 403)
        self.assertEqual(Student.objects.count(), 3)
