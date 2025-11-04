from django.urls import path
from . import views

urlpatterns = [
    path("", views.module_list, name="module_list"),
    path("create/", views.module_create, name="module_create"),
    path("update/", views.module_update, name="module_update"),  # URI via GET
    path("delete/", views.module_delete, name="module_delete"),  # URI via GET
    path('generate_quiz/', views.generate_quiz, name='generate_quiz'),
    path('summarize/', views.summarize_module, name='summarize_module'),
]
