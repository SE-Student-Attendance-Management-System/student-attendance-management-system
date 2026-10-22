
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    User,
    Student,
    Faculty,
    Course,
    ClassSection,
    Enrollment,
    AttendanceSession,
    AttendanceRecord,
    AttendanceAudit,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Attendance System", {"fields": ("role",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Attendance System", {"fields": ("role",)}),
    )


admin.site.register(Student)
admin.site.register(Faculty)
admin.site.register(Course)
admin.site.register(ClassSection)
admin.site.register(Enrollment)
admin.site.register(AttendanceSession)
admin.site.register(AttendanceRecord)
admin.site.register(AttendanceAudit)
