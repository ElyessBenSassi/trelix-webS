from django import forms
from .models import Examen

class ExamenForm(forms.ModelForm):
    class Meta:
        model = Examen
        fields = ['nom', 'description', 'note_max', 'date_examen']
        labels = {
            'nom': "Nom de l'examen",
            'description': "Description",
            'note_max': "Note maximale",
            'date_examen': "Date de l'examen",
        }
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Ex: Examen Web Sémantique"}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': "Décrire brièvement l'examen..."}),
            'note_max': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': "Ex: 20", 'min': 1}),
            'date_examen': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
