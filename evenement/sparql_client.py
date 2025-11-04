from SPARQLWrapper import SPARQLWrapper, JSON, POST

FUSEKI_URL = "http://localhost:3030/trelix"
BASE_URI = "http://example.com/evenement/"

def insert_evenement(uri, typeEvenement, nomEvenement, description, lieu, dateDebut, dateFin, image=None):
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/update")
    sparql.setMethod(POST)

    # Échapper les guillemets dans les chaînes
    nomEvenement = nomEvenement.replace('"', '\\"')
    description = description.replace('"', '\\"')
    lieu = lieu.replace('"', '\\"')

    image_triple = ""
    if image and image != "":
        image = image.replace('"', '\\"')
        image_triple = f'ex:image "{image}" ;'

    query = f"""
    PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    
    INSERT DATA {{
        <{BASE_URI}{uri}> a ex:{typeEvenement} ;
            ex:nomEvenement "{nomEvenement}" ;
            ex:description "{description}" ;
            ex:lieu "{lieu}" ;
            ex:dateDebut "{dateDebut}"^^xsd:dateTime ;
            ex:dateFin "{dateFin}"^^xsd:dateTime ;
            {image_triple}
            .
    }}
    """

    sparql.setQuery(query)
    sparql.query()

def get_evenement_by_uri(uri):
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/query")
    sparql.setQuery(f"""
    PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
    SELECT ?evenement ?typeEvenement ?nomEvenement ?description ?lieu ?dateDebut ?dateFin ?image
    WHERE {{
        <{BASE_URI}{uri}> a ?typeEvenement ;
                   ex:nomEvenement ?nomEvenement ;
                   ex:description ?description ;
                   ex:lieu ?lieu ;
                   ex:dateDebut ?dateDebut ;
                   ex:dateFin ?dateFin ;
                   ex:image ?image .
    }}
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    if results["results"]["bindings"]:
        r = results["results"]["bindings"][0]
        return {
            "uri": uri,
            "typeEvenement": r["typeEvenement"]["value"].split("#")[-1].replace("Event", ""),
            "nomEvenement": r["nomEvenement"]["value"],
            "description": r["description"]["value"],
            "lieu": r["lieu"]["value"],
            "dateDebut": r["dateDebut"]["value"],
            "dateFin": r["dateFin"]["value"],
            "image": r["image"]["value"],
        }
    return None


def get_evenements():
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/query")
    sparql.setQuery(f"""
    PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
    SELECT ?evenement ?typeEvenement ?nomEvenement ?description ?lieu ?dateDebut ?dateFin ?image
    WHERE {{
        ?evenement a ?typeEvenement ;
                   ex:nomEvenement ?nomEvenement ;
                   ex:description ?description ;
                   ex:lieu ?lieu ;
                   ex:dateDebut ?dateDebut ;
                   ex:dateFin ?dateFin ;
                   ex:image ?image .
        FILTER (?typeEvenement IN (ex:HackathonEvent, ex:WorkshopEvent))
    }}
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    print(f"🔍 Nombre d'événements récupérés: {len(results['results']['bindings'])}")
    
    evenements = []
    for r in results["results"]["bindings"]:
        event_data = {
            "uri": r["evenement"]["value"].replace(BASE_URI, ""),
            "typeEvenement": r["typeEvenement"]["value"].split("#")[-1],
            "nomEvenement": r["nomEvenement"]["value"],
            "description": r["description"]["value"],
            "lieu": r["lieu"]["value"],
            "dateDebut": r["dateDebut"]["value"],
            "dateFin": r["dateFin"]["value"],
            "image": r["image"]["value"] if "image" in r else "",
        }
        print(f"📄 Événement: {event_data['nomEvenement']}, Image: {event_data['image']}")
        evenements.append(event_data)
    
    return evenements


def update_evenement(uri, typeEvenement, nomEvenement, description, lieu, dateDebut, dateFin, image):
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/update")
    sparql.setMethod(POST)
    query = f"""
    PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
    DELETE {{
        <{BASE_URI}{uri}> ?p ?o .
    }}
    INSERT {{
        <{BASE_URI}{uri}> a ex:{typeEvenement} ;
            ex:nomEvenement "{nomEvenement}" ;
            ex:description "{description}" ;
            ex:lieu "{lieu}" ;
            ex:dateDebut "{dateDebut}" ;
            ex:dateFin "{dateFin}" ;
            ex:image "{image}" .
    }}
    WHERE {{
        <{BASE_URI}{uri}> ?p ?o .
    }}
    """
    sparql.setQuery(query)
    sparql.query()


def delete_evenement(uri):
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/update")
    sparql.setMethod(POST)
    sparql.setQuery(f"""
    PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
    DELETE WHERE {{
        <{BASE_URI}{uri}> ?p ?o
    }}
    """)
    sparql.query()


def add_participation(etudiant_uri, evenement_uri):
    """Ajoute une participation en utilisant la propriété 'participer' existante"""
    query = f"""
    PREFIX ns: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
    
    INSERT DATA {{
        <{etudiant_uri}> ns:participer <{evenement_uri}> .
    }}
    """
    return update_sparql(query)


def query_sparql(query):
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/query")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


def update_sparql(query):
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/update")
    sparql.setMethod(POST)
    sparql.setQuery(query)
    return sparql.query()


def check_participation(etudiant_uri, evenement_uri):
    """Vérifie si un étudiant participe déjà à un événement"""
    query = f"""
    PREFIX ns: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
    
    ASK {{
        <{etudiant_uri}> ns:participer <{evenement_uri}> .
    }}
    """
    response = query_sparql(query)
    return response['boolean'] if 'boolean' in response else False


def get_participations(etudiant_uri):
    """Récupère tous les événements auxquels participe un étudiant"""
    query = f"""
    PREFIX ns: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
    
    SELECT ?evenement ?nom ?type ?dateDebut ?dateFin ?lieu ?description ?image
    WHERE {{
        <{etudiant_uri}> ns:participer ?evenement .
        ?evenement ns:nomEvenement ?nom .
        ?evenement ns:typeEvenement ?type .
        ?evenement ns:dateDebut ?dateDebut .
        ?evenement ns:dateFin ?dateFin .
        ?evenement ns:lieu ?lieu .
        ?evenement ns:description ?description .
        OPTIONAL {{ ?evenement ns:image ?image . }}
    }}
    """
    return query_sparql(query)


    
