from SPARQLWrapper import SPARQLWrapper, POST
import uuid

FUSEKI_URL = "http://localhost:3030/trelix"
BASE_URI = "http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#"

def generate_uri(label):
    safe = label.replace(" ", "_")
    return f"{safe}{uuid.uuid4().hex[:8]}"

def insert_preference(uri, langue, formatCours, periode, vacances, modeEtude):
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/update")
    sparql.setMethod(POST)
    sparql.setQuery(f"""
    PREFIX ex: <{BASE_URI}>
    INSERT DATA {{
        <{BASE_URI}{uri}> a ex:Preference ;
            ex:langue "{langue}" ;
            ex:formatCours "{formatCours}" ;
            ex:periode "{periode}" ;
            ex:vacances "{vacances}" ;
            ex:modeEtude "{modeEtude}" .
    }}
    """)
    sparql.query()


def get_preferences():
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/query")
    sparql.setQuery(f"""
    PREFIX ex: <{BASE_URI}>
    SELECT ?uri ?langue ?formatCours ?periode ?vacances ?modeEtude
    WHERE {{
      ?uri a ex:Preference ;
            ex:langue ?langue ;
            ex:formatCours ?formatCours ;
            ex:periode ?periode ;
            ex:vacances ?vacances ;
            ex:modeEtude ?modeEtude .
    }}
    """)
    sparql.setReturnFormat("json")
    results = sparql.query().convert()
    data = []
    for r in results["results"]["bindings"]:
        data.append({
            "uri": r["uri"]["value"],
            "langue": r["langue"]["value"],
            "formatCours": r["formatCours"]["value"],
            "periode": r["periode"]["value"],
            "vacances": r["vacances"]["value"],
            "modeEtude": r["modeEtude"]["value"],
        })
    return data


def update_preference(uri, langue, formatCours, periode, vacances, modeEtude):
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/update")
    sparql.setMethod(POST)
    sparql.setQuery(f"""
    PREFIX ex: <{BASE_URI}>
    DELETE WHERE {{ <{uri}> ?p ?o }};
    INSERT DATA {{
        <{uri}> a ex:Preference ;
            ex:langue "{langue}" ;
            ex:formatCours "{formatCours}" ;
            ex:periode "{periode}" ;
            ex:vacances "{vacances}" ;
            ex:modeEtude "{modeEtude}" .
    }}
    """)
    sparql.query()


def delete_preference(uri):
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/update")
    sparql.setMethod(POST)
    sparql.setQuery(f"""
    DELETE WHERE {{ <{uri}> ?p ?o }}
    """)
    sparql.query()
