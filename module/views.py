import uuid
import urllib.parse
import json
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse

from .sparql_client import insert_module, get_modules, update_module, delete_module, get_module_content
from .semantic_search import semantic_search
from huggingface_hub import InferenceClient
import requests



# Génération automatique d'une URI "safe"
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
    uri = urllib.parse.unquote(uri)  # décoder l'URI

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

def generate_quiz(request):
    uri = request.GET.get("uri")
    if not uri:
        return JsonResponse({"error": "Module URI missing"}, status=400)

    content = get_module_content(uri)
    if not content:
        return JsonResponse({"error": "Module has no content"}, status=400)

    client = InferenceClient(token=settings.HF_API_TOKEN)

    prompt = f"""
Créez un petit quiz (3 questions) en français basé sur le texte suivant :
---
{content}
---
Chaque question doit avoir 3 options (A, B, C) et indiquer laquelle est correcte.
Format strictement en JSON, comme ceci :
[
  {{
    "question": "...",
    "options": ["A", "B", "C"],
    "answer": "A"
  }},
  ...
]
Ne fournissez aucun texte ou explication supplémentaire en dehors du tableau JSON.
"""

    completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3-0324",
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = completion.choices[0].message["content"]

    try:
        clean_text = raw_text.strip().strip("```").replace("json", "").strip()
        quiz_json = json.loads(clean_text)
        for q in quiz_json:
            q['options'] = [{"label": opt, "value": opt} for opt in q.get('options', [])]
    except json.JSONDecodeError:
        quiz_json = []

    return JsonResponse({"quiz": quiz_json})

def summarize_module(request):
    """
    Génère un résumé du contenu du module à partir de son URI.
    """
    uri = request.GET.get("uri")
    if not uri:
        return JsonResponse({"error": "Module URI missing"}, status=400)

    content = get_module_content(uri)
    if not content:
        return JsonResponse({"error": "Module has no content"}, status=400)

    url = f"https://api.nlpcloud.io/v1/{settings.NLP_CLOUD_MODEL}/summarization"
    headers = {
        "Authorization": f"Token {settings.NLP_CLOUD_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": content,
        "min_length": 50,
        "max_length": 300
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            data = response.json()
            summary = data.get("summary_text", "")
            return JsonResponse({"summary": summary})
        else:
            return JsonResponse({"error": f"NLP API returned status {response.status_code}"}, status=response.status_code)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

from django.http import JsonResponse
import json

def semantic_search_view(request):
    """
    Vue pour la recherche sémantique avec support des requêtes en langage naturel.
    Compatible avec POST JSON ou GET classique.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            query = data.get("query", "").strip()
        except Exception as e:
            return JsonResponse({"error": f"Invalid JSON: {e}"}, status=400)
    else:
        query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse({"error": "Missing query"}, status=400)

    try:
        print(f"🧠 Requête utilisateur : {query}")
        results = semantic_search(query)
        print(f"✅ {len(results)} résultats trouvés")

        return JsonResponse({
            "success": True,
            "query": query,
            "count": len(results),
            "results": results
        })
    except Exception as e:
        print(f"💥 Erreur recherche sémantique : {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)
