from django.urls import path
from . import views

app_name = 'person'

urlpatterns = [
    path('signup/', views.sign_up, name='sign_up'),
    path('signin/', views.sign_in, name='sign_in'),
    path('signout/', views.sign_out, name='sign_out'),
    path('admin/persons/', views.admin_persons, name='admin_persons'),
    path('admin/persons/<path:person_uri>/edit/', views.admin_person_edit, name='admin_person_edit'),
    path('admin/persons/<path:person_uri>/delete/', views.admin_person_delete, name='admin_person_delete'),
]

