from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from . import student_views

urlpatterns = [
    # Authentication & Landing Routes (Issue #11 / PR #27)
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path("", views.home, name="home"),

    # Course & Class Section Management Routes (Issue #20 / PR #26)
    path("courses/", views.course_list, name="course_list"),
    path("courses/create/", views.course_create, name="course_create"),
    path("courses/<int:pk>/edit/", views.course_update, name="course_update"),
    path(
        "courses/<int:pk>/sections/<int:section_pk>/edit/",
        views.section_update,
        name="section_update",
    ),
    # Student Management (Issues #14 and #15)
    path("students/", student_views.student_list, name="student_list"),
    path("students/create/", student_views.student_create, name="student_create"),
    path("students/search/", student_views.student_search, name="student_search"),
    path("students/<int:pk>/", student_views.student_detail, name="student_detail"),
    path("students/<int:pk>/edit/", student_views.student_update, name="student_update"),
]
