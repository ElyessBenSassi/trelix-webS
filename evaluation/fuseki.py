import requests

FUSEKI_URL = "http://localhost:3030/webfinalle2"
PREFIX = "http://localhost:3030/webfinalle2/examen/"

def envoyer_examen_fuseki(examen):
    badge_value = examen.badge.type if examen.badge else "None"


    data = f"""
    PREFIX ex: <{PREFIX}>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    DELETE WHERE {{
        <{PREFIX}{examen.id}> ?p ?o .
    }};

    INSERT DATA {{
        <{PREFIX}{examen.id}> 
            ex:nom "{examen.nom}" ;
            ex:description "{examen.description}" ;
            ex:noteMax "{examen.note_max}"^^xsd:integer ;
            ex:dateExamen "{examen.date_examen}"^^xsd:date ;
            ex:badge "{badge_value}" .
    }}
    """

    headers = {"Content-Type": "application/sparql-update"}
    response = requests.post(f"{FUSEKI_URL}/update", data=data.encode('utf-8'), headers=headers)
    print("✅ Fuseki upsert Examen+Badge:", response.status_code)
    print("📌 Response:", response.text)


def supprimer_examen_fuseki(exam_id):
    data = f"""
    PREFIX ex: <{PREFIX}>
    DELETE WHERE {{ <{PREFIX}{exam_id}> ?p ?o . }}
    """
    
    headers = {"Content-Type": "application/sparql-update"}
    response = requests.post(f"{FUSEKI_URL}/update", data=data.encode("utf-8"), headers=headers)

    print("🗑 Suppression Fuseki:", response.status_code)
    print("📌 Response:", response.text)
