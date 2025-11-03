import uuid
import urllib.parse
from django.shortcuts import render, redirect
from .sparql_client import insert_module, get_modules, update_module, delete_module

# Génération automatique d'une URI “safe”
def generate_uri(nomModule):
    safe_name = nomModule.replace(" ", "_")
    return f"{safe_name}{uuid.uuid4().hex[:8]}"

# Liste de tous les modules
def module_list(request):
    modules = get_modules()
    return render(request, "module/list.html", {"modules": modules})

# Création d'un module
def module_create(request):
    if request.method == "POST":
        nomModule = request.POST["nomModule"]
        NomCours = request.POST["NomCours"]
        Contenu = request.POST["Contenu"]

        uri = generate_uri(nomModule)  # URI auto

        insert_module(uri, nomModule, NomCours, Contenu)
        return redirect("module_list")
    return render(request, "module/form.html")

# Modification d'un module existant
def module_update(request):
    uri = request.GET.get("uri")
    if not uri:
        return redirect("module_list")
    uri = urllib.parse.unquote(uri)  # décoder l’URI

    modules = get_modules()
    module = next((m for m in modules if m["uri"] == uri), None)

    if request.method == "POST":
        nomModule = request.POST["nomModule"]
        NomCours = request.POST["NomCours"]
        Contenu = request.POST["Contenu"]

        update_module(uri, nomModule, NomCours, Contenu)
        return redirect("module_list")

    return render(request, "module/form.html", {"module": module})

# Suppression d'un module
def module_delete(request):
    uri = request.GET.get("uri")
    if uri:
        uri = urllib.parse.unquote(uri)
        delete_module(uri)
    return redirect("module_list")
