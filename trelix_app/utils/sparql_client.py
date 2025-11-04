# trelix_app/utils/sparql_client.py
from SPARQLWrapper import SPARQLWrapper, JSON, POST

FUSEKI_URL = "http://localhost:3030/trelix"

def run_select(query):
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results['results']['bindings']

def run_update(update_query):
    sparql = SPARQLWrapper(f"{FUSEKI_URL}/update")
    sparql.setMethod(POST)
    sparql.setQuery(update_query)
    sparql.query()
