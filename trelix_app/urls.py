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
    path('activity/', include('activity.urls')),
    path('person/', include('person.urls')),
]
