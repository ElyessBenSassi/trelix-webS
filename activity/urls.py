from django.urls import path
from . import views

app_name = 'activity'

urlpatterns = [
    path('', views.activity_list, name='activity_list'),
    path('create/', views.activity_create, name='activity_create'),
    path('detail/<path:activity_uri>/', views.activity_detail, name='activity_detail'),
    path('edit/<path:activity_uri>/', views.activity_edit, name='activity_edit'),
    path('delete/<path:activity_uri>/', views.activity_delete, name='activity_delete'),
]
