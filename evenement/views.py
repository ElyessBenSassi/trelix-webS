import uuid, urllib.parse, os
from django.shortcuts import render, redirect
from django.conf import settings
from .sparql_client import insert_evenement, add_participation, check_participation, get_participations, get_evenements, update_evenement, delete_evenement, get_evenement_by_uri
import google.generativeai as genai
import json
from django.http import JsonResponse
import requests
import io
import time
from PIL import Image, ImageDraw, ImageFilter
from django.core.files import File
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Configuration de l'API Gemini (existant)
genai.configure(api_key=settings.GOOGLE_API_KEY)

# =============================================================================
# RECHERCHE SÉMANTIQUE AVEC GOOGLE GEMINI
# =============================================================================

@csrf_exempt
def semantic_search(request):
    """Recherche sémantique avec Google Gemini"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '').strip()
            
            if not query:
                return JsonResponse({'error': 'La requête est vide'}, status=400)
            
            print(f"🔍 Recherche sémantique: '{query}'")
            
            # Générer une requête SPARQL avec Gemini
            sparql_query = generate_semantic_sparql(query)
            
            if not sparql_query:
                return JsonResponse({'error': 'Impossible de générer la requête'}, status=500)
            
            # Exécuter la requête SPARQL
            results = execute_semantic_search(sparql_query)
            
            return JsonResponse({
                'success': True,
                'results': results,
                'query': query,
                'count': len(results)
            })
            
        except Exception as e:
            print(f"❌ Erreur recherche sémantique: {str(e)}")
            return JsonResponse({'error': f'Erreur: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=400)

def generate_semantic_sparql(natural_language_query):
    """Génère une requête SPARQL avec Google Gemini"""
    try:
        print(f"🔗 Utilisation de Gemini pour: {natural_language_query}")
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        Tu es un expert SPARQL. Convertis cette requête en langage naturel en une requête SPARQL valide.
        
        Ontologie:
        - Prefix: ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
        - Classes: HackathonEvent, WorkshopEvent
        - Propriétés: nomEvenement, description, lieu, dateDebut, dateFin, image
        - Base URI: http://example.com/evenement/

        Règles IMPORTANTES:
        1. TOUJOURS sélectionner: ?evenement ?nomEvenement ?description ?lieu ?dateDebut ?dateFin ?image
        2. Le champ ?evenement doit avoir l'URI complète
        3. Utiliser FILTER avec regex pour la recherche texte
        4. Réponds UNIQUEMENT avec la requête SPARQL complète, sans explications

        Exemples:
        - "événements qui commencent par M" → FILTER regex(?nomEvenement, "^M", "i")
        - "hackathons à Paris" → FILTER regex(?lieu, "Paris", "i") && ?evenement a ex:HackathonEvent
        - "workshops sur l'IA" → FILTER regex(?description, "IA", "i") && ?evenement a ex:WorkshopEvent
        - "événements de ce mois" → FILTER (month(?dateDebut) = month(now()) && year(?dateDebut) = year(now()))

        Requête à convertir: "{natural_language_query}"
        """
        
        response = model.generate_content(prompt)
        sparql_query = response.text.strip()
        
        # Nettoyer la réponse
        sparql_query = sparql_query.replace('```sparql', '').replace('```', '').strip()
        
        print(f"📝 Requête SPARQL générée: {sparql_query}")
        return sparql_query
        
    except Exception as e:
        print(f"❌ Erreur Gemini: {str(e)}")
        return generate_fallback_sparql(natural_language_query)

def generate_fallback_sparql(query):
    """Fallback intelligent sans IA - Version améliorée"""
    query_lower = query.lower()
    
    print(f"🔄 Utilisation du fallback pour: {query}")
    
    # Détection des motifs courants
    words = query_lower.split()
    
    # Recherche par première lettre
    if any(word in ['commence', 'début', 'start', 'première', 'lettre'] for word in words):
        for word in words:
            if len(word) == 1 and word.isalpha():
                letter = word.upper()
                return f"""
                PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
                SELECT ?evenement ?nomEvenement ?description ?lieu ?dateDebut ?dateFin ?image
                WHERE {{
                    ?evenement a ?type ;
                             ex:nomEvenement ?nomEvenement ;
                             ex:description ?description ;
                             ex:lieu ?lieu ;
                             ex:dateDebut ?dateDebut ;
                             ex:dateFin ?dateFin ;
                             OPTIONAL {{ ?evenement ex:image ?image . }}
                    FILTER (regex(?nomEvenement, "^{letter}", "i"))
                }}
                """
        # Si pas de lettre trouvée mais la requête contient "par X"
        if 'par' in words:
            idx = words.index('par')
            if idx + 1 < len(words) and len(words[idx + 1]) == 1:
                letter = words[idx + 1].upper()
                return f"""
                PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
                SELECT ?evenement ?nomEvenement ?description ?lieu ?dateDebut ?dateFin ?image
                WHERE {{
                    ?evenement a ?type ;
                             ex:nomEvenement ?nomEvenement ;
                             ex:description ?description ;
                             ex:lieu ?lieu ;
                             ex:dateDebut ?dateDebut ;
                             ex:dateFin ?dateFin ;
                             OPTIONAL {{ ?evenement ex:image ?image . }}
                    FILTER (regex(?nomEvenement, "^{letter}", "i"))
                }}
                """
    
    # Recherche par type d'événement
    event_type = None
    if any(word in ['hackathon', 'hack'] for word in words):
        event_type = "HackathonEvent"
    elif any(word in ['workshop', 'atelier'] for word in words):
        event_type = "WorkshopEvent"
    
    # Recherche par lieu
    location = None
    location_keywords = ['à', 'dans', 'ville', 'lieu', 'place', 'localisation', 'paris', 'france', 'afrique']
    for word in words:
        if word in location_keywords:
            # Chercher le mot suivant comme lieu
            idx = words.index(word)
            if idx + 1 < len(words) and len(words[idx + 1]) > 2:
                location = words[idx + 1].capitalize()
                break
    
    # Recherche par contenu
    content_keywords = ['intelligence', 'artificielle', 'ia', 'ai', 'technologie', 'programmation']
    content = None
    for word in words:
        if word in content_keywords:
            content = word
            break
    
    # Construction de la requête
    conditions = []
    
    if event_type:
        conditions.append(f"?evenement a ex:{event_type}")
    
    if location:
        conditions.append(f'FILTER (regex(?lieu, "{location}", "i"))')
    
    if content:
        conditions.append(f'FILTER (regex(?description, "{content}", "i"))')
    
    # Si pas de conditions spécifiques, recherche générale
    if not conditions:
        # Nettoyer la query pour la recherche
        clean_query = " ".join([word for word in words if len(word) > 2])
        if clean_query:
            conditions.append(f'FILTER (regex(?nomEvenement, "{clean_query}", "i") || regex(?description, "{clean_query}", "i") || regex(?lieu, "{clean_query}", "i"))')
        else:
            conditions.append(f'FILTER (regex(?nomEvenement, "{query}", "i") || regex(?description, "{query}", "i") || regex(?lieu, "{query}", "i"))')
    
    where_clause = " ;\n                 ".join(conditions)
    
    sparql_query = f"""
    PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
    SELECT ?evenement ?nomEvenement ?description ?lieu ?dateDebut ?dateFin ?image
    WHERE {{
        ?evenement a ?type ;
                 ex:nomEvenement ?nomEvenement ;
                 ex:description ?description ;
                 ex:lieu ?lieu ;
                 ex:dateDebut ?dateDebut ;
                 ex:dateFin ?dateFin ;
                 OPTIONAL {{ ?evenement ex:image ?image . }}
        {where_clause}
    }}
    """
    
    print(f"📝 Requête fallback générée: {sparql_query}")
    return sparql_query

def execute_semantic_search(sparql_query):
    """Exécute la requête SPARQL et retourne les résultats"""
    try:
        from SPARQLWrapper import SPARQLWrapper, JSON
        
        sparql = SPARQLWrapper("http://localhost:3030/trelix/query")
        sparql.setQuery(sparql_query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        
        events = []
        for r in results["results"]["bindings"]:
            event_uri = r["evenement"]["value"]
            event_id = event_uri.replace("http://example.com/evenement/", "")
            
            event_data = {
                "uri": event_id,
                "nomEvenement": r["nomEvenement"]["value"],
                "description": r["description"]["value"],
                "lieu": r["lieu"]["value"],
                "dateDebut": r["dateDebut"]["value"],
                "dateFin": r["dateFin"]["value"],
                "image": r.get("image", {}).get("value", "") if "image" in r else "",
            }
            events.append(event_data)
        
        print(f"✅ {len(events)} événements trouvés")
        return events
        
    except Exception as e:
        print(f"❌ Erreur exécution SPARQL: {str(e)}")
        return []

# =============================================================================
# VUES EXISTANTES
# =============================================================================

@login_required
def participer_evenement(request, uri):
    etudiant_uri = request.session.get("user_uri")

    if not etudiant_uri:
        messages.error(request, "Vous devez être connecté pour participer.")
        return redirect("person:sign_in")

    evenement_uri = f"http://example.com/evenement/{uri}"

    # Ajouter participation
    add_participation(etudiant_uri, evenement_uri)

    messages.success(request, "Votre participation a été enregistrée ✅")
    return redirect("evenement:detail_evenement", uri=uri)

@login_required
def mes_participations(request):
    etudiant_uri = request.session.get("user_uri")

    if not etudiant_uri:
        messages.error(request, "Vous devez être connecté pour voir vos participations.")
        return redirect("person:sign_in")

    participations = get_participations(etudiant_uri)

    events = []
    for r in participations["results"]["bindings"]:
        events.append({
            "uri": r["evenement"]["value"].replace("http://example.com/evenement/", ""),
            "nom": r["nom"]["value"],
            "dateDebut": r["dateDebut"]["value"],
            "dateFin": r["dateFin"]["value"],
            "lieu": r["lieu"]["value"],
            "description": r["description"]["value"],
            "image": r.get("image", {}).get("value", "")
        })

    return render(request, "evenement/mes_participations.html", {
        "events": events
    })

def generate_real_image(prompt):
    """Génère une VRAIE image avec Flux API (GRATUIT)"""
    try:
        print(f"🚀 Génération d'image avec Flux: {prompt}")
        
        # API Flux - GRATUITE et fonctionnelle
        API_URL = "https://flux1.aiwan.io/api/v1/generation/image-to-image"
        
        payload = {
            "prompt": prompt,
            "width": 512,
            "height": 512,
            "guidance_scale": 7.5,
            "num_inference_steps": 20
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        print("📡 Envoi à Flux API...")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        
        print(f"📥 Réponse: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "images" in data and len(data["images"]) > 0:
                # L'API retourne une image en base64
                import base64
                image_data = data["images"][0]
                if image_data.startswith('data:image'):
                    image_data = image_data.split(',')[1]
                image_bytes = base64.b64decode(image_data)
                print("✅ Image générée avec succès!")
                return image_bytes
        else:
            print(f"❌ Erreur Flux API: {response.status_code} - {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Erreur Flux: {str(e)}")
    
    # Fallback: Essayer avec une autre API gratuite
    return try_alternative_api(prompt)

def try_alternative_api(prompt):
    """Essaye une autre API gratuite"""
    try:
        print("🔄 Essai avec alternative API...")
        
        # API alternative gratuite
        API_URL = "https://api-inference.banana.dev/run/black-forest-labs/FLUX-1-schnell"
        
        payload = {
            "prompt": prompt,
            "width": 512,
            "height": 512
        }
        
        response = requests.post(API_URL, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if "image" in data:
                import base64
                image_bytes = base64.b64decode(data["image"])
                print("✅ Alternative API fonctionne!")
                return image_bytes
                
    except Exception as e:
        print(f"❌ Alternative API échouée: {e}")
    
    return None

def create_simple_image(title, event_type):
    """Crée une image simple mais BELLE (pas juste du texte)"""
    try:
        import random
        
        width, height = 512, 512
        
        # Créer un dégradé de couleur
        color1 = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
        color2 = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
        
        # Créer un dégradé
        image = Image.new('RGB', (width, height), color1)
        draw = ImageDraw.Draw(image)
        
        for i in range(height):
            ratio = i / height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        
        # Ajouter des éléments graphiques
        # Cercles décoratifs
        for _ in range(5):
            x = random.randint(50, width-50)
            y = random.randint(50, height-50)
            radius = random.randint(20, 80)
            draw.ellipse([x-radius, y-radius, x+radius, y+radius], 
                        fill=(255, 255, 255, 50), outline=(255, 255, 255, 100))
        
        # Ajouter du texte stylisé
        try:
            from PIL import ImageFont
            # Essayer différentes polices
            fonts = []
            try:
                fonts.append(ImageFont.truetype("arial.ttf", 36))
                fonts.append(ImageFont.truetype("arialbd.ttf", 28))
            except:
                try:
                    fonts.append(ImageFont.load_default())
                except:
                    pass
            
            if fonts:
                # Titre principal
                title_font = fonts[0]
                bbox = draw.textbbox((0, 0), title, font=title_font)
                text_width = bbox[2] - bbox[0]
                x = (width - text_width) / 2
                draw.text((x, 180), title, fill=(255, 255, 255), font=title_font)
                
                # Sous-titre
                if len(fonts) > 1:
                    subtitle_font = fonts[1]
                    subtitle = f"{event_type} Event"
                    bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
                    text_width = bbox[2] - bbox[0]
                    x = (width - text_width) / 2
                    draw.text((x, 230), subtitle, fill=(255, 255, 255, 180), font=subtitle_font)
        
        except Exception as e:
            print(f"Note: Police non disponible - {e}")
        
        # Ajouter un effet de flou artistique
        image = image.filter(ImageFilter.GaussianBlur(1))
        
        return image
        
    except Exception as e:
        print(f"❌ Erreur création image: {e}")
        return None

@csrf_exempt
def generate_image(request):
    """Vue pour générer une image via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title', '').strip()
            event_type = data.get('event_type', '').strip()

            if not title:
                return JsonResponse({'error': 'Le titre est requis'}, status=400)

            print(f"🎨 Génération d'image: '{title}' - Type: '{event_type}'")

            # Prompt optimisé
            prompt = f"professional {event_type} event banner titled '{title}', modern design, vibrant colors, high quality, attractive"
            
            # Essayer d'abord les APIs externes
            image_bytes = generate_real_image(prompt)
            
            if image_bytes:
                # ✅ Succès avec API externe
                image = Image.open(io.BytesIO(image_bytes))
                image_type = "api"
            else:
                # 🔄 Créer une image graphique locale
                print("🔄 Création d'image graphique locale...")
                image = create_simple_image(title, event_type)
                image_type = "local"
                if not image:
                    return JsonResponse({
                        'error': 'Impossible de générer une image. Veuillez uploader une image manuellement.'
                    }, status=500)

            # Sauvegarder l'image
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')[:30]
            
            if image_type == "api":
                image_name = f"ai_generated_{safe_title}_{uuid.uuid4().hex[:8]}.jpg"
            else:
                image_name = f"graphic_{safe_title}_{uuid.uuid4().hex[:8]}.jpg"
                
            image_path = image_name
            full_image_path = os.path.join(settings.MEDIA_ROOT, image_path)

            image.save(full_image_path, format='JPEG', quality=90, optimize=True)
            print(f"💾 Image sauvegardée: {image_path}")

            return JsonResponse({
                'success': True,
                'image_url': f"{settings.MEDIA_URL}{image_path}",
                'image_path': image_path,
                'message': 'Image générée avec succès!'
            })

        except Exception as e:
            print(f"❌ Erreur génération image: {str(e)}")
            return JsonResponse({'error': f'Erreur: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=400)

def ai_generate_description(title, event_type):
    """Génère une description d'événement"""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        Génère une description détaillée et engageante en français pour un événement de type "{event_type}" avec le titre "{title}".
        
        La description doit :
        - Être en français
        - Faire 3-4 lignes maximum
        - Être engageante et professionnelle
        - Inclure les bénéfices pour les participants
        
        Réponse en français uniquement :
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    
    except Exception as e:
        return f"Erreur lors de la génération: {str(e)}"

@csrf_exempt
def generate_description(request):
    """Vue pour générer la description via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title', '').strip()
            event_type = data.get('event_type', '').strip()
            
            if not title:
                return JsonResponse({'error': 'Le titre est requis'}, status=400)
            
            description = ai_generate_description(title, event_type)
            return JsonResponse({'description': description})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

def generate_uri(nomEvenement):
    safe = nomEvenement.replace(" ", "_")
    return f"{safe}{uuid.uuid4().hex[:8]}"

def evenement_list(request):
    evenements = get_evenements()
    return render(request, "evenement/list.html", {"evenements": evenements})

def evenement_listadmin(request):
    evenements = get_evenements()
    return render(request, "evenement/listadmin.html", {"evenements": evenements})

def detail_evenement(request, uri):
    evenement = get_evenement_by_uri(uri)
    deja_participe = False
    if request.session.get('user_uri'):
        etudiant_uri = request.session['user_uri']
        evenement_full_uri = f"http://example.com/evenement/{uri}"
        deja_participe = check_participation(etudiant_uri, evenement_full_uri)

    context = {
        'evenement': evenement,
        'deja_participe': deja_participe
    }
    return render(request, 'evenement/detail.html', context)

def evenement_create(request):
    if request.method == "POST":
        try:
            typeEvenement = request.POST["typeEvenement"]
            nomEvenement = request.POST["nomEvenement"]
            description = request.POST["description"]
            lieu = request.POST["lieu"]
            dateDebut = request.POST["dateDebut"]
            dateFin = request.POST["dateFin"]

            typeEvenementClass = f"{typeEvenement}Event"

            image_path = ""
            image_file = request.FILES.get("image")
            generated_image_path = request.POST.get("generated_image_path", "")

            print(f"🖼️ Image générée reçue: {generated_image_path}")
            print(f"📁 Fichier image uploadé: {image_file}")

            # Gestion des images
            if image_file:
                # Image uploadée manuellement
                save_path = os.path.join(settings.MEDIA_ROOT, image_file.name)
                with open(save_path, "wb+") as dest:
                    for chunk in image_file.chunks():
                        dest.write(chunk)
                image_path = image_file.name
                print(f"✅ Image uploadée: {image_path}")
                    
            elif generated_image_path:
                # Image générée par IA
                image_path = generated_image_path
                print(f"✅ Utilisation image générée: {image_path}")
            else:
                print("⚠️ Aucune image fournie")

            uri = generate_uri(nomEvenement)
            
            # DEBUG: Afficher les données avant insertion
            print(f"📝 Données à insérer:")
            print(f"  URI: {uri}")
            print(f"  Type: {typeEvenementClass}")
            print(f"  Nom: {nomEvenement}")
            print(f"  Image: {image_path}")
            
            insert_evenement(uri, typeEvenementClass, nomEvenement, description, lieu, dateDebut, dateFin, image_path)

            print(f"✅ Événement créé: {nomEvenement}")
            return redirect("evenement:evenement_list")

        except Exception as e:
            print(f"❌ Erreur création événement: {e}")
            return render(request, "evenement/form.html", {'error': str(e)})

    return render(request, "evenement/form.html")

def evenement_update(request):
    uri = urllib.parse.unquote(request.GET.get("uri", ""))
    evenements = get_evenements()
    evenement = next((e for e in evenements if e["uri"] == uri), None)
    if not evenement:
        return redirect("evenement:evenement_list")

    if request.method == "POST":
        typeEvenement = request.POST["typeEvenement"]
        nomEvenement = request.POST["nomEvenement"]
        description = request.POST["description"]
        lieu = request.POST["lieu"]
        dateDebut = request.POST["dateDebut"]
        dateFin = request.POST["dateFin"]

        typeEvenementClass = f"{typeEvenement}Event"

        image_file = request.FILES.get("image")
        generated_image_path = request.POST.get("generated_image_path", "")
        image_path = evenement["image"]

        if image_file:
            save_path = os.path.join(settings.MEDIA_ROOT, image_file.name)
            with open(save_path, "wb+") as dest:
                for chunk in image_file.chunks():
                    dest.write(chunk)
            image_path = image_file.name
        elif generated_image_path:
            image_path = generated_image_path

        update_evenement(uri, typeEvenementClass, nomEvenement, description, lieu, dateDebut, dateFin, image_path)

        return redirect("evenement:evenement_list")

    return render(request, "evenement/form.html", {"evenement": evenement})

def evenement_delete(request):
    uri = request.GET.get("uri")
    if uri:
        uri = urllib.parse.unquote(uri)
        delete_evenement(uri)
    return redirect("evenement:evenement_list")