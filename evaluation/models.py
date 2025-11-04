from django.db import models


class Badge(models.Model):
    type = models.CharField(max_length=50)
    image = models.ImageField(upload_to='badges/', blank=True, null=True)

    def __str__(self):
        return self.type


class Examen(models.Model):
    nom = models.CharField(max_length=200)
    date_examen = models.DateField()
    note_max = models.FloatField()
    description = models.TextField(blank=True, null=True)

    # ✅ Lien vers Badge
    badge = models.ForeignKey(Badge, on_delete=models.SET_NULL, null=True, blank=True, related_name="examens")

    def __str__(self):
        return self.nom
