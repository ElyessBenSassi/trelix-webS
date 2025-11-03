"""
URL configuration for trelix_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from .views import classes_html_view
from . import views  # ✅ importer views


urlpatterns = [
       path('', views.home, name='home'),
       path('classes/', classes_html_view),
       path("modules/", include("module.urls")),
       path("produit/", include("produit.urls")),
       path('admin/', admin.site.urls),
       path('evenements/', include('evenement.urls')),
       path("preferences/", include("preference.urls")),



]
