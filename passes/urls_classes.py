from django.urls import path
from . import views

urlpatterns = [
    path("", views.class_list, name="list"),
    path("<int:class_id>/roster/", views.class_roster, name="roster"),
    path("propose/", views.propose_class, name="propose"),
    path("proposals/", views.my_proposals, name="proposals"),
]
