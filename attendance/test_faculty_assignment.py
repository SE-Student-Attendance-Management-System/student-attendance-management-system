
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Course, ClassSection, Faculty


User = get_user_model()


class FacultyAssignmentDashboardTests(TestCase):
    def setUp(self):
        self.faculty_user = User.objects.create_user(
            username="faculty_one",
            password="test-password-123",
            role=User.Role.FACULTY,
        )
        self.faculty = Faculty.objects.create(
            faculty_code="FAC201",
            user=self.faculty_user,
            name="Professor One",
            email="professor.one@example.com",
            department="CSE",
        )

        self.other_faculty_user = User.objects.create_user(
            username="faculty_two",
            password="test-password-123",
            role=User.Role.FACULTY,
        )
        self.other_faculty = Faculty.objects.create(
            faculty_code="FAC202",
            user=self.other_faculty_user,
            name="Professor Two",
            email="professor.two@example.com",
            department="ECE",
        )

        self.own_course = Course.objects.create(
            course_code="CS201",
            course_name="My Assigned Course",
            semester=3,
        )
        self.own_section = ClassSection.objects.create(
            course=self.own_course,
            faculty=self.faculty,
            section="A",
            academic_term="2026-27",
        )

        self.other_course = Course.objects.create(
            course_code="CS202",
            course_name="Other Faculty Course",
            semester=3,
        )
        self.other_section = ClassSection.objects.create(
            course=self.other_course,
            faculty=self.other_faculty,
            section="B",
            academic_term="2026-27",
        )

    def test_faculty_sees_own_assigned_classes(self):
        self.client.force_login(self.faculty_user)

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Assigned Course")
        self.assertContains(response, "Section A")

    def test_faculty_cannot_see_other_facultys_classes(self):
        self.client.force_login(self.faculty_user)

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Assigned Course")
        self.assertNotContains(response, "Other Faculty Course")
        self.assertNotContains(response, "Section B")

    def test_unassigned_faculty_sees_no_assigned_classes(self):
        unassigned_user = User.objects.create_user(
            username="faculty_three",
            password="test-password-123",
            role=User.Role.FACULTY,
        )
        Faculty.objects.create(
            faculty_code="FAC203",
            user=unassigned_user,
            name="Professor Three",
            email="professor.three@example.com",
            department="CSE",
        )

        self.client.force_login(unassigned_user)
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "No class sections currently assigned to your profile.",
        )
        self.assertNotContains(response, "My Assigned Course")
        self.assertNotContains(response, "Other Faculty Course")
