from django.shortcuts import render, redirect, get_object_or_404
from .models import Examen
from .forms import ExamenForm
from .utils import creer_achievement_automatique
from .fuseki import envoyer_examen_fuseki, supprimer_examen_fuseki


from django.db.models import Q

def examen_list(request):
    search = request.GET.get('search', '')  # recherche par texte
    order = request.GET.get('order', '-id')  # tri par défaut : derniers d'abord

    examens = Examen.objects.all()

    if search:
        examens = examens.filter(
            Q(nom__icontains=search) |
            Q(description__icontains=search) |
            Q(note_max__icontains=search)
        )

    examens = examens.order_by(order)

    return render(request, 'examens_list.html', {
        'examens': examens,
        'search': search,
        'order': order
    })


def examen_ajouter(request):
    if request.method == "POST":
        form = ExamenForm(request.POST)
        if form.is_valid():
            examen = form.save()
            creer_achievement_automatique(examen)
            envoyer_examen_fuseki(examen)
            return redirect('/api/')
    else:
        form = ExamenForm()
    return render(request, 'examen_form.html', {'form': form, 'title': "Ajouter un examen"})


def examen_modifier(request, id):
    examen = get_object_or_404(Examen, id=id)
    if request.method == "POST":
        form = ExamenForm(request.POST, instance=examen)
        if form.is_valid():
            examen = form.save()
            creer_achievement_automatique(examen)
            envoyer_examen_fuseki(examen)
            return redirect('/api/examens/')
    else:
        form = ExamenForm(instance=examen)
    return render(request, 'examen_form.html', {'form': form, 'title': "Modifier un examen"})


def examen_supprimer(request, id):
    examen = get_object_or_404(Examen, id=id)
    examen.delete()
    supprimer_examen_fuseki(id)
    return redirect('/api/examens/')
