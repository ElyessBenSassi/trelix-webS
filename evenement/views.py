import uuid, urllib.parse
from django.shortcuts import render, redirect
from .sparql_client import insert_evenement, get_evenements, update_evenement, delete_evenement

def generate_uri(nomEvenement):
    safe = nomEvenement.replace(" ", "_")
    return f"{safe}{uuid.uuid4().hex[:8]}"

def evenement_list(request):
    evenements = get_evenements()
    return render(request, "evenement/list.html", {"evenements": evenements})

def evenement_create(request):
    if request.method == "POST":
        nomEvenement = request.POST["nomEvenement"]
        dateEvenement = request.POST["dateEvenement"]
        description = request.POST["description"]
        lieu = request.POST["lieu"]

        uri = generate_uri(nomEvenement)
        insert_evenement(uri, nomEvenement, dateEvenement, description, lieu)
        return redirect("evenement:evenement_list")  # ✅ namespace ajouté
    return render(request, "evenement/form.html")

def evenement_update(request):
    uri = request.GET.get("uri")
    if not uri:
        return redirect("evenement:evenement_list")  # ✅ namespace ajouté
    uri = urllib.parse.unquote(uri)
    evenements = get_evenements()
    evenement = next((e for e in evenements if e["uri"] == uri), None)

    if request.method == "POST":
        nomEvenement = request.POST["nomEvenement"]
        dateEvenement = request.POST["dateEvenement"]
        description = request.POST["description"]
        lieu = request.POST["lieu"]
        update_evenement(uri, nomEvenement, dateEvenement, description, lieu)
        return redirect("evenement:evenement_list")  # ✅ namespace ajouté

    return render(request, "evenement/form.html", {"evenement": evenement})

def evenement_delete(request):
    uri = request.GET.get("uri")
    if uri:
        uri = urllib.parse.unquote(uri)
        delete_evenement(uri)
    return redirect("evenement:evenement_list")  # ✅ namespace ajouté
