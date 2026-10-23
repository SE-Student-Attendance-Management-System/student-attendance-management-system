
from django.urls import path

from . import views

urlpatterns = [
    path("courses/", views.course_list, name="course_list"),
    path("courses/create/", views.course_create, name="course_create"),
    path("courses/<int:pk>/edit/", views.course_update, name="course_update"),
    path(
        "courses/<int:pk>/sections/<int:section_pk>/edit/",
        views.section_update,
        name="section_update",
    ),
]
