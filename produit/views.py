import uuid
import urllib.parse
from django.shortcuts import render, redirect
from .sparql_client import insert_produit, get_produits, update_produit, delete_produit

def generate_uri(nomPack):
    safe_name = nomPack.replace(" ", "_")
    return f"{safe_name}{uuid.uuid4().hex[:8]}"

def produit_list(request):
    produits = get_produits()
    return render(request, "produit/list.html", {"produits": produits})

def produit_create(request):
    if request.method == "POST":
        nomPack = request.POST["nomPack"]
        description = request.POST["description"]
        valeurMonetaire = request.POST["valeurMonetaire"]

        uri = generate_uri(nomPack)
        insert_produit(uri, nomPack, description, valeurMonetaire)
        return redirect("produit_list")

    return render(request, "produit/form.html")

def produit_update(request):
    uri = request.GET.get("uri")
    if not uri:
        return redirect("produit_list")
    uri = urllib.parse.unquote(uri)

    produits = get_produits()
    produit = next((p for p in produits if p["uri"] == uri), None)

    if request.method == "POST":
        nomPack = request.POST["nomPack"]
        description = request.POST["description"]
        valeurMonetaire = request.POST["valeurMonetaire"]

        update_produit(uri, nomPack, description, valeurMonetaire)
        return redirect("produit_list")

    return render(request, "produit/form.html", {"produit": produit})

def produit_delete(request):
    uri = request.GET.get("uri")
    if uri:
        uri = urllib.parse.unquote(uri)
        delete_produit(uri)
    return redirect("produit_list")
