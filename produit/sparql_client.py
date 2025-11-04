from SPARQLWrapper import SPARQLWrapper, JSON, POST

FUSEKI_URL = "http://localhost:3030/trelix"
BASE_URI = "http://example.com/produit/"

def insert_produit(uri, nomPack, description, valeurMonetaire):
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/update")
    sparql.setMethod(POST)
    sparql.setQuery(f"""
    PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
    INSERT DATA {{
        <{BASE_URI}{uri}> a ex:Produit ;
            ex:nomPack "{nomPack}" ;
            ex:description "{description}" ;
            ex:valeurMonetaire "{valeurMonetaire}" .
    }}
    """)
    sparql.query()

def get_produits():
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/query")
    sparql.setQuery(f"""
    PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
    SELECT ?produit ?nomPack ?description ?valeurMonetaire
    WHERE {{
        ?produit a ex:Produit ;
                 ex:nomPack ?nomPack ;
                 ex:description ?description ;
                 ex:valeurMonetaire ?valeurMonetaire .
    }}
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    produits = []
    for r in results["results"]["bindings"]:
        produits.append({
            "uri": r["produit"]["value"].replace(BASE_URI, ""),
            "nomPack": r["nomPack"]["value"],
            "description": r["description"]["value"],
            "valeurMonetaire": r["valeurMonetaire"]["value"],
        })
    return produits

def update_produit(uri, nomPack=None, description=None, valeurMonetaire=None):
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/update")
    sparql.setMethod(POST)
    updates = []

    if nomPack:
        updates.append(f"""
        PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
        DELETE {{ <{BASE_URI}{uri}> ex:nomPack ?o }}
        INSERT {{ <{BASE_URI}{uri}> ex:nomPack "{nomPack}" }}
        WHERE {{ <{BASE_URI}{uri}> ex:nomPack ?o }}
        """)
    if description:
        updates.append(f"""
        PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
        DELETE {{ <{BASE_URI}{uri}> ex:description ?o }}
        INSERT {{ <{BASE_URI}{uri}> ex:description "{description}" }}
        WHERE {{ <{BASE_URI}{uri}> ex:description ?o }}
        """)
    if valeurMonetaire:
        updates.append(f"""
        PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
        DELETE {{ <{BASE_URI}{uri}> ex:valeurMonetaire ?o }}
        INSERT {{ <{BASE_URI}{uri}> ex:valeurMonetaire "{valeurMonetaire}" }}
        WHERE {{ <{BASE_URI}{uri}> ex:valeurMonetaire ?o }}
        """)

    for q in updates:
        sparql.setQuery(q)
        sparql.query()


def delete_produit(uri):
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/update")
    sparql.setMethod(POST)
    sparql.setQuery(f"""
    PREFIX ex: <http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#>
    DELETE WHERE {{
        <{BASE_URI}{uri}> ?p ?o
    }}
    """)
    sparql.query()
