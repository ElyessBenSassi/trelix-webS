from django.urls import path
from . import views

app_name = "preference"

urlpatterns = [
    path("", views.preference_list, name="preference_list"),
    path("create/", views.preference_create, name="preference_create"),
    path("update/", views.preference_update, name="preference_update"),
    path("delete/", views.preference_delete, name="preference_delete"),
]
