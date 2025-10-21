from django.urls import path
from . import views
urlpatterns = [
    path("", views.submission_list, name="list"),
    path("new/", views.submission_create, name="new"),
    path("<int:pk>/approve/", views.submission_approve, name="approve"),
    path("<int:pk>/reject/", views.submission_reject, name="reject"),
]
