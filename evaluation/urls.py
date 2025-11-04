from django.urls import path
from . import views

urlpatterns = [
    path('', views.examen_list, name='examen_list'),
    path('examens/ajouter/', views.examen_ajouter, name='examen_ajouter'),
    path('examens/modifier/<int:id>/', views.examen_modifier, name='examen_modifier'),
    path('examens/supprimer/<int:id>/', views.examen_supprimer, name='examen_supprimer'),
]