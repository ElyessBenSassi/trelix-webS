from django.contrib import admin
from django.urls import path, include
from .views import classes_html_view
from . import views 
from django.conf import settings
from django.conf.urls.static import static 


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
    path('api/', include('evaluation.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
