import urllib.parse
from django.shortcuts import render, redirect
from .sparql_client import insert_preference, get_preferences, update_preference, delete_preference, generate_uri

def preference_list(request):
    prefs = get_preferences()
    return render(request, "preference/list.html", {"preferences": prefs})

def preference_create(request):
    if request.method == "POST":
        langue = request.POST["langue"]
        formatCours = request.POST["formatCours"]
        periode = request.POST["periode"]
        vacances = request.POST["vacances"]
        modeEtude = request.POST["modeEtude"]

        uri = generate_uri(langue)
        insert_preference(uri, langue, formatCours, periode, vacances, modeEtude)
        return redirect("preference:preference_list")
    return render(request, "preference/form.html")

def preference_update(request):
    uri = request.GET.get("uri")
    if not uri:
        return redirect("preference:preference_list")

    uri = urllib.parse.unquote(uri)
    prefs = get_preferences()
    pref = next((p for p in prefs if p["uri"] == uri), None)

    if request.method == "POST":
        langue = request.POST["langue"]
        formatCours = request.POST["formatCours"]
        periode = request.POST["periode"]
        vacances = request.POST["vacances"]
        modeEtude = request.POST["modeEtude"]
        update_preference(uri, langue, formatCours, periode, vacances, modeEtude)
        return redirect("preference:preference_list")

    return render(request, "preference/form.html", {"preference": pref})

def preference_delete(request):
    uri = request.GET.get("uri")
    if uri:
        uri = urllib.parse.unquote(uri)
        delete_preference(uri)
    return redirect("preference:preference_list")
