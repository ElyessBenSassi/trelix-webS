from django.contrib import admin
from .models import Badge, Examen


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'image')


@admin.register(Examen)
class ExamenAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'date_examen', 'note_max', 'badge')
