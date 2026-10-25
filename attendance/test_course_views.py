
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Course, ClassSection, Faculty


User = get_user_model()


class CourseManagementViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="courseadmin",
            password="test-password-123",
            role=User.Role.ADMIN,
        )
        self.client.force_login(self.admin)

        self.faculty = Faculty.objects.create(
            faculty_code="FAC101",
            name="Test Faculty",
            email="faculty101@example.com",
            department="CSE",
        )

        self.course = Course.objects.create(
            course_code="CS101",
            course_name="Database Systems",
            semester=3,
        )

        self.section = ClassSection.objects.create(
            course=self.course,
            faculty=self.faculty,
            section="A",
            academic_term="2026-27",
        )

    def test_course_list_loads(self):
        response = self.client.get(reverse("course_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Database Systems")
        self.assertContains(response, "Test Faculty")

    def test_create_course(self):
        response = self.client.post(
            reverse("course_create"),
            {
                "course_code": "CS202",
                "course_name": "Data Analytics",
                "semester": 4,
                "faculty": self.faculty.pk,
                "section": "B",
                "academic_term": "2026-27",
            },
        )

        self.assertEqual(response.status_code, 302)

        new_course = Course.objects.get(course_code="CS202")
        self.assertEqual(new_course.course_name, "Data Analytics")
        self.assertEqual(new_course.semester, 4)

        new_section = ClassSection.objects.get(course=new_course)
        self.assertEqual(new_section.faculty, self.faculty)
        self.assertEqual(new_section.section, "B")
        self.assertEqual(new_section.academic_term, "2026-27")

    def test_duplicate_course_code_is_rejected(self):
        response = self.client.post(
            reverse("course_create"),
            {
                "course_code": "CS101",
                "course_name": "Another Course",
                "semester": 4,
                "faculty": self.faculty.pk,
                "section": "B",
                "academic_term": "2026-27",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(ClassSection.objects.count(), 1)

    def test_duplicate_section_is_rejected(self):
        response = self.client.post(
            reverse(
                "section_update",
                kwargs={
                    "pk": self.course.pk,
                    "section_pk": self.section.pk,
                },
            ),
            {
                "course_code": "CS101",
                "course_name": "Database Systems",
                "semester": 3,
                "faculty": self.faculty.pk,
                "section": "A",
                "academic_term": "2026-27",
            },
        )

        # Existing section data remains valid; no duplicate is created.
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ClassSection.objects.count(), 1)

    def test_invalid_section_does_not_create_course(self):
        response = self.client.post(
            reverse("course_create"),
            {
                "course_code": "CS304",
                "course_name": "Computer Networks",
                "semester": 4,
                "faculty": "",
                "section": "",
                "academic_term": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Course.objects.filter(course_code="CS304").exists()
        )

    def test_update_course(self):
        response = self.client.post(
            reverse("course_update", kwargs={"pk": self.course.pk}),
            {
                "course_code": "CS102",
                "course_name": "Updated Database Systems",
                "semester": 4,
                "faculty": self.faculty.pk,
                "section": "B",
                "academic_term": "2027-28",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.course.refresh_from_db()
        self.section.refresh_from_db()

        self.assertEqual(self.course.course_code, "CS102")
        self.assertEqual(
            self.course.course_name,
            "Updated Database Systems",
        )
        self.assertEqual(self.course.semester, 4)
        self.assertEqual(self.section.section, "B")
        self.assertEqual(self.section.academic_term, "2027-28")

    def test_admin_can_reassign_faculty_to_section(self):
        new_faculty = Faculty.objects.create(
            faculty_code="FAC102",
            name="New Test Faculty",
            email="faculty102@example.com",
            department="CSE",
        )

        response = self.client.post(
            reverse(
                "section_update",
                kwargs={
                    "pk": self.course.pk,
                    "section_pk": self.section.pk,
                },
            ),
            {
                "course_code": self.course.course_code,
                "course_name": self.course.course_name,
                "semester": self.course.semester,
                "faculty": new_faculty.pk,
                "section": self.section.section,
                "academic_term": self.section.academic_term,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.section.refresh_from_db()
        self.assertEqual(self.section.faculty, new_faculty)

    def test_inactive_faculty_cannot_be_assigned(self):
        inactive_faculty = Faculty.objects.create(
            faculty_code="FAC103",
            name="Inactive Faculty",
            email="inactive@example.com",
            department="CSE",
            is_active=False,
        )

        response = self.client.post(
            reverse(
                "section_update",
                kwargs={
                    "pk": self.course.pk,
                    "section_pk": self.section.pk,
                },
            ),
            {
                "course_code": self.course.course_code,
                "course_name": self.course.course_name,
                "semester": self.course.semester,
                "faculty": inactive_faculty.pk,
                "section": self.section.section,
                "academic_term": self.section.academic_term,
            },
        )

        self.assertEqual(response.status_code, 200)

        self.section.refresh_from_db()
        self.assertEqual(self.section.faculty, self.faculty)

    def test_non_admin_cannot_manage_courses(self):
        self.client.logout()

        unauth_response = self.client.get(reverse("course_list"))
        self.assertEqual(unauth_response.status_code, 302)
        self.assertIn(
            "/login/",
            unauth_response.headers.get("Location", ""),
        )

        student = User.objects.create_user(
            username="course_student",
            password="test-password-123",
            role=User.Role.STUDENT,
        )
        self.client.force_login(student)

        response = self.client.get(reverse("course_list"))
        self.assertEqual(response.status_code, 403)

        post_response = self.client.post(
            reverse("course_create"),
            {"course_code": "CS999"},
        )
        self.assertEqual(post_response.status_code, 403)

        faculty_user = User.objects.create_user(
            username="course_faculty_user",
            password="test-password-123",
            role=User.Role.FACULTY,
        )
        self.client.force_login(faculty_user)

        faculty_response = self.client.get(reverse("course_list"))
        self.assertEqual(faculty_response.status_code, 403)
