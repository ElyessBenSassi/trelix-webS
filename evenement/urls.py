from django.urls import path
from . import views


app_name = "evenement"  # ✅ très important pour le namespace


urlpatterns = [
    path("", views.evenement_list, name="evenement_list"),
    path("create/", views.evenement_create, name="evenement_create"),
    path("update/", views.evenement_update, name="evenement_update"),
    path("delete/", views.evenement_delete, name="evenement_delete"),
]
