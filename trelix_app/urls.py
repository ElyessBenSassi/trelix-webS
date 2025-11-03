from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),  
    path('classes/', views.classes_html_view),
    path('activity/', include('activity.urls')),
    path('person/', include('person.urls')),
]
