from django.urls import path
from . import views

urlpatterns = [
    path("", views.class_list, name="list"),
    path("propose/", views.propose_class, name="propose"),
    path("proposals/", views.my_proposals, name="proposals"),
]
