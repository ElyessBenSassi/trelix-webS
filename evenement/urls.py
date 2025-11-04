from django.urls import path
from . import views


app_name = "evenement"  # ✅ très important pour le namespace


urlpatterns = [
    path("", views.evenement_list, name="evenement_list"),
    path("create/", views.evenement_create, name="evenement_create"),
    path("update/", views.evenement_update, name="evenement_update"),
    path("delete/", views.evenement_delete, name="evenement_delete"),
    path("listadmin/", views.evenement_listadmin, name="evenement_list"),
    path("detail/<str:uri>/", views.detail_evenement, name="detail_evenement"),  # Nouvelle route
    path("generate-description/", views.generate_description, name="generate_description"),  # Nouvelle route
    path("generate-image/", views.generate_image, name="generate_image"),
    path("participer/<str:uri>/", views.participer_evenement, name="participer_evenement"),
    path("mes-participations/", views.mes_participations, name="mes_participations"),



]
