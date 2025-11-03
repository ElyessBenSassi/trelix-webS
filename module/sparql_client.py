from SPARQLWrapper import SPARQLWrapper, JSON, POST

FUSEKI_URL = "http://localhost:3030/trelix"
BASE_URI = "http://example.com/module/"

def insert_module(uri, nomModule, NomCours, Contenu):
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/update")
    sparql.setMethod(POST)
    sparql.setQuery(f"""
    PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
    INSERT DATA {{
        <{BASE_URI}{uri}> a ex:Module ;
            ex:nomModule "{nomModule}" ;
            ex:NomCours "{NomCours}" ;
            ex:Contenu "{Contenu}" .
    }}
    """)
    sparql.query()

def get_modules():
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/query")
    sparql.setQuery(f"""
    PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
    SELECT ?module ?nomModule ?NomCours ?Contenu
    WHERE {{
        ?module a ex:Module ;
                ex:nomModule ?nomModule ;
                ex:NomCours ?NomCours ;
                ex:Contenu ?Contenu .
    }}
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    modules = []
    for r in results["results"]["bindings"]:
        modules.append({
            "uri": r["module"]["value"].replace(BASE_URI, ""),  # URI “safe” pour Django
            "nomModule": r["nomModule"]["value"],
            "NomCours": r["NomCours"]["value"],
            "Contenu": r["Contenu"]["value"],
        })
    return modules

def update_module(uri, nomModule=None, NomCours=None, Contenu=None):
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/update")
    sparql.setMethod(POST)

    # Préfixe unique déclaré une seule fois
    query = f"""
    PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>

    DELETE {{
        <{BASE_URI}{uri}> ex:nomModule ?oldNomModule .
        <{BASE_URI}{uri}> ex:NomCours ?oldNomCours .
        <{BASE_URI}{uri}> ex:Contenu ?oldContenu .
    }}
    INSERT {{
    """

    # Ajouter uniquement les champs qui ont changé
    if nomModule:
        query += f'        <{BASE_URI}{uri}> ex:nomModule "{nomModule}" .\n'
    if NomCours:
        query += f'        <{BASE_URI}{uri}> ex:NomCours "{NomCours}" .\n'
    if Contenu:
        query += f'        <{BASE_URI}{uri}> ex:Contenu "{Contenu}" .\n'

    query += f"""
    }}
    WHERE {{
        OPTIONAL {{ <{BASE_URI}{uri}> ex:nomModule ?oldNomModule . }}
        OPTIONAL {{ <{BASE_URI}{uri}> ex:NomCours ?oldNomCours . }}
        OPTIONAL {{ <{BASE_URI}{uri}> ex:Contenu ?oldContenu . }}
    }}
    """

    sparql.setQuery(query)
    sparql.query()


def delete_module(uri):
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/update")
    sparql.setMethod(POST)
    sparql.setQuery(f"""
    PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
    DELETE WHERE {{
        <{BASE_URI}{uri}> ?p ?o
    }}
    """)
    sparql.query()
