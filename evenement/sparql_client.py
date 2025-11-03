from SPARQLWrapper import SPARQLWrapper, JSON, POST

FUSEKI_URL = "http://localhost:3030/trelix"
BASE_URI = "http://example.com/evenement/"

def insert_evenement(uri, nomEvenement, dateEvenement, description, lieu):
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/update")
    sparql.setMethod(POST)
    sparql.setQuery(f"""
    PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
    INSERT DATA {{
        <{BASE_URI}{uri}> a ex:Evenement ;
            ex:nomEvenement "{nomEvenement}" ;
            ex:dateEvenement "{dateEvenement}" ;
            ex:description "{description}" ;
            ex:lieu "{lieu}" .
    }}
    """)
    sparql.query()

def get_evenements():
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/query")
    sparql.setQuery(f"""
    PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
    SELECT ?evenement ?nomEvenement ?dateEvenement ?description ?lieu
    WHERE {{
        ?evenement a ex:Evenement ;
                   ex:nomEvenement ?nomEvenement ;
                   ex:dateEvenement ?dateEvenement ;
                   ex:description ?description ;
                   ex:lieu ?lieu .
    }}
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    evenements = []
    for r in results["results"]["bindings"]:
        evenements.append({
            "uri": r["evenement"]["value"].replace(BASE_URI, ""),
            "nomEvenement": r["nomEvenement"]["value"],
            "dateEvenement": r["dateEvenement"]["value"],
            "description": r["description"]["value"],
            "lieu": r["lieu"]["value"],
        })
    return evenements


def update_evenement(uri, nomEvenement=None, dateEvenement=None, description=None, lieu=None):
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/update")
    sparql.setMethod(POST)
    query = f"""
    PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>

    DELETE {{
        <{BASE_URI}{uri}> ex:nomEvenement ?oldNom .
        <{BASE_URI}{uri}> ex:dateEvenement ?oldDate .
        <{BASE_URI}{uri}> ex:description ?oldDesc .
        <{BASE_URI}{uri}> ex:lieu ?oldLieu .
    }}
    INSERT {{
    """

    if nomEvenement:
        query += f'        <{BASE_URI}{uri}> ex:nomEvenement "{nomEvenement}" .\n'
    if dateEvenement:
        query += f'        <{BASE_URI}{uri}> ex:dateEvenement "{dateEvenement}" .\n'
    if description:
        query += f'        <{BASE_URI}{uri}> ex:description "{description}" .\n'
    if lieu:
        query += f'        <{BASE_URI}{uri}> ex:lieu "{lieu}" .\n'

    query += f"""
    }}
    WHERE {{
        OPTIONAL {{ <{BASE_URI}{uri}> ex:nomEvenement ?oldNom . }}
        OPTIONAL {{ <{BASE_URI}{uri}> ex:dateEvenement ?oldDate . }}
        OPTIONAL {{ <{BASE_URI}{uri}> ex:description ?oldDesc . }}
        OPTIONAL {{ <{BASE_URI}{uri}> ex:lieu ?oldLieu . }}
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
