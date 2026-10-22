
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        FACULTY = "FACULTY", "Faculty"
        STUDENT = "STUDENT", "Student"

    username = models.CharField(max_length=50, unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )


class Student(models.Model):
    student_id = models.BigAutoField(primary_key=True)
    usn = models.CharField(max_length=15, unique=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_profile",
    )
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    phone = models.CharField(max_length=15, blank=True)
    program = models.CharField(max_length=50)
    semester = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(99)]
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.usn} - {self.name}"


class Faculty(models.Model):
    faculty_id = models.BigAutoField(primary_key=True)
    faculty_code = models.CharField(max_length=15, unique=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="faculty_profile",
    )
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    department = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.faculty_code} - {self.name}"


class Course(models.Model):
    course_id = models.BigAutoField(primary_key=True)
    course_code = models.CharField(max_length=20, unique=True)
    course_name = models.CharField(max_length=100)
    semester = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(99)]
    )

    def __str__(self):
        return f"{self.course_code} - {self.course_name}"


class ClassSection(models.Model):
    class_section_id = models.BigAutoField(primary_key=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="class_sections",
    )
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.PROTECT,
        related_name="class_sections",
    )
    section = models.CharField(max_length=20)
    academic_term = models.CharField(max_length=20)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["course", "section", "academic_term"],
                name="unique_course_section_term",
            )
        ]

    def __str__(self):
        return f"{self.course.course_code} - {self.section} ({self.academic_term})"


class Enrollment(models.Model):
    enrollment_id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    class_section = models.ForeignKey(
        ClassSection,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "class_section"],
                name="unique_student_class_enrollment",
            )
        ]

    def __str__(self):
        return f"{self.student.usn} - {self.class_section}"


class AttendanceSession(models.Model):
    session_id = models.BigAutoField(primary_key=True)
    class_section = models.ForeignKey(
        ClassSection,
        on_delete=models.PROTECT,
        related_name="attendance_sessions",
    )
    session_date = models.DateField()
    session_no = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["class_section", "session_date", "session_no"],
                name="unique_section_session_date_number",
            )
        ]

    def __str__(self):
        return f"{self.class_section} - {self.session_date} (Session {self.session_no})"


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"

    attendance_id = models.BigAutoField(primary_key=True)
    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.PROTECT,
        related_name="attendance_records",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name="attendance_records",
    )
    status = models.CharField(max_length=10, choices=Status.choices)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="marked_attendance_records",
    )
    marked_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["session", "student"],
                name="unique_student_attendance_per_session",
            )
        ]
        indexes = [
            models.Index(fields=["student", "session"]),
        ]

    def __str__(self):
        return f"{self.student.usn} - {self.session} - {self.status}"


class AttendanceAudit(models.Model):
    audit_id = models.BigAutoField(primary_key=True)
    attendance = models.ForeignKey(
        AttendanceRecord,
        on_delete=models.PROTECT,
        related_name="audit_entries",
    )
    old_status = models.CharField(
        max_length=10,
        choices=AttendanceRecord.Status.choices,
    )
    new_status = models.CharField(
        max_length=10,
        choices=AttendanceRecord.Status.choices,
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="attendance_audit_entries",
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attendance {self.attendance_id}: {self.old_status} -> {self.new_status}"
