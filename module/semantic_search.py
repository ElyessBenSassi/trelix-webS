from huggingface_hub import InferenceClient
from django.conf import settings
from SPARQLWrapper import SPARQLWrapper, JSON
import json
import re

FUSEKI_URL = "http://localhost:3030/trelix"
BASE_URI = "http://example.com/module/"

def semantic_search(query):
    """
    Utilise un modèle LLM pour convertir une requête en langage naturel
    en une requête SPARQL, puis exécute cette requête sur Fuseki.
    """
    # Initialiser le client HuggingFace
    client = InferenceClient(token=settings.HF_API_TOKEN)
    
    # Prompt pour générer la requête SPARQL
    prompt = f"""Tu es un expert en SPARQL et en recherche sémantique. 
Convertis la requête suivante en une requête SPARQL pour rechercher des modules d'apprentissage.

Les modules ont ces propriétés:
- ex:nomModule (nom du module)
- ex:NomCours (nom du cours)
- ex:Contenu (contenu textuel du module)

Préfixe à utiliser:
PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>

Requête utilisateur: "{query}"

Génère UNIQUEMENT la requête SPARQL SELECT sans explication. La requête doit:
1. Rechercher dans tous les champs (nomModule, NomCours, Contenu)
2. Utiliser FILTER avec REGEX pour la recherche (insensible à la casse)
3. Retourner: ?module ?nomModule ?NomCours ?Contenu
4. Utiliser OPTIONAL pour gérer les propriétés manquantes

Exemple de format attendu:
PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
SELECT ?module ?nomModule ?NomCours ?Contenu
WHERE {{
    ?module a ex:Module .
    OPTIONAL {{ ?module ex:nomModule ?nomModule . }}
    OPTIONAL {{ ?module ex:NomCours ?NomCours . }}
    OPTIONAL {{ ?module ex:Contenu ?Contenu . }}
    FILTER (
        REGEX(?nomModule, "mot-clé", "i") ||
        REGEX(?NomCours, "mot-clé", "i") ||
        REGEX(?Contenu, "mot-clé", "i")
    )
}}

Réponds UNIQUEMENT avec la requête SPARQL, sans markdown ni explication."""

    try:
        # Appel au modèle DeepSeek
        completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3-0324",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        
        sparql_query = completion.choices[0].message["content"].strip()
        
        # Nettoyer la réponse (enlever markdown si présent)
        sparql_query = re.sub(r'```sparql\n|```\n|```', '', sparql_query).strip()
        
        print(f"Generated SPARQL Query:\n{sparql_query}")
        
        # Exécuter la requête SPARQL sur Fuseki
        results = execute_sparql_query(sparql_query)
        
        return results
        
    except Exception as e:
        print(f"Erreur lors de la recherche sémantique: {e}")
        # Fallback: recherche simple par mot-clé
        return fallback_search(query)

def execute_sparql_query(sparql_query):
    """
    Exécute une requête SPARQL sur Fuseki et retourne les résultats formatés
    """
    try:
        sparql = SPARQLWrapper(f"{FUSEKI_URL}/query")
        sparql.setQuery(sparql_query)
        sparql.setReturnFormat(JSON)
        
        results = sparql.query().convert()
        
        modules = []
        for r in results["results"]["bindings"]:
            module_data = {
                "uri": r.get("module", {}).get("value", "").replace(BASE_URI, ""),
                "nomModule": r.get("nomModule", {}).get("value", ""),
                "NomCours": r.get("NomCours", {}).get("value", ""),
                "Contenu": r.get("Contenu", {}).get("value", ""),
            }
            modules.append(module_data)
        
        return modules
        
    except Exception as e:
        print(f"Erreur lors de l'exécution de la requête SPARQL: {e}")
        return []

def fallback_search(query):
    """
    Recherche simple par mot-clé en cas d'échec de la recherche sémantique
    """
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/query")
    
    # Échapper les caractères spéciaux pour REGEX
    safe_query = query.replace('\\', '\\\\').replace('"', '\\"')
    
    sparql_query = f"""
    PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
    SELECT ?module ?nomModule ?NomCours ?Contenu
    WHERE {{
        ?module a ex:Module .
        OPTIONAL {{ ?module ex:nomModule ?nomModule . }}
        OPTIONAL {{ ?module ex:NomCours ?NomCours . }}
        OPTIONAL {{ ?module ex:Contenu ?Contenu . }}
        FILTER (
            REGEX(?nomModule, "{safe_query}", "i") ||
            REGEX(?NomCours, "{safe_query}", "i") ||
            REGEX(?Contenu, "{safe_query}", "i")
        )
    }}
    """
    
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    
    try:
        results = sparql.query().convert()
        modules = []
        for r in results["results"]["bindings"]:
            modules.append({
                "uri": r.get("module", {}).get("value", "").replace(BASE_URI, ""),
                "nomModule": r.get("nomModule", {}).get("value", ""),
                "NomCours": r.get("NomCours", {}).get("value", ""),
                "Contenu": r.get("Contenu", {}).get("value", ""),
            })
        return modules
    except Exception as e:
        print(f"Erreur lors de la recherche fallback: {e}")
        return []