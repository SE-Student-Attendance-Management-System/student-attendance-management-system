from django.contrib.auth import get_user_model
from django.test import TestCase

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
        response = self.client.get("/courses/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Database Systems")

    def test_create_course(self):
        response = self.client.post(
            "/courses/create/",
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
        self.assertTrue(
            Course.objects.filter(
                course_code="CS202",
                course_name="Data Analytics",
                semester=4,
            ).exists()
        )

        new_course = Course.objects.get(course_code="CS202")
        self.assertTrue(
            ClassSection.objects.filter(
                course=new_course,
                faculty=self.faculty,
                section="B",
                academic_term="2026-27",
            ).exists()
        )

    def test_duplicate_course_code_is_rejected(self):
        response = self.client.post(
            "/courses/create/",
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
            f"/courses/{self.course.pk}/sections/{self.section.pk}/edit/",
            {
                "course_code": "CS101",
                "course_name": "Database Systems",
                "semester": 3,
                "faculty": self.faculty.pk,
                "section": "A",
                "academic_term": "2026-27",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ClassSection.objects.count(), 1)

    def test_invalid_section_does_not_create_course(self):
        response = self.client.post(
            "/courses/create/",
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
            f"/courses/{self.course.pk}/edit/",
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

    def test_non_admin_cannot_manage_courses(self):
        self.client.logout()

        student = User.objects.create_user(
            username="course_student",
            password="test-password-123",
            role=User.Role.STUDENT,
        )
        self.client.force_login(student)

        response = self.client.get("/courses/")
        self.assertEqual(response.status_code, 302)
