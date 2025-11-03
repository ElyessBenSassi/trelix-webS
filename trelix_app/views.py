from django.shortcuts import render
from SPARQLWrapper import SPARQLWrapper, JSON

def classes_html_view(request):
    sparql = SPARQLWrapper("http://localhost:3030/trelix/sparql")
    sparql.setQuery("""
        SELECT ?class
        WHERE {
          ?class a <http://www.w3.org/2002/07/owl#Class> .
        }
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    # Extract class URIs
    class_uris = [binding['class']['value'] for binding in results['results']['bindings']]
    return render(request, 'trelix_app/classes.html', {'class_uris': class_uris})