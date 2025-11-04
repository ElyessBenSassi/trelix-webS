from SPARQLWrapper import SPARQLWrapper, JSON, POST
from typing import List, Dict, Optional
import time


class ActivitySPARQLService:
    ONTOLOGY_NS = "http://www.semanticweb.org/elyes/ontologies/2025/10/activity-personne-5/"
    # Alternative namespace for hasInstructor property
    ALT_ONTOLOGY_NS = "http://www.semanticweb.org/elyes/ontologies/2025/10/person-activity/"
    ACTIVITY_CLASS = f"{ONTOLOGY_NS}activity"
    ACTIVITY_NAME_PROPERTY = f"{ONTOLOGY_NS}activityName"
    DESCRIPTION_PROPERTY = f"{ONTOLOGY_NS}activityDescription"
    DURATION_PROPERTY = f"{ONTOLOGY_NS}activityDuration"
    START_DATE_PROPERTY = f"{ONTOLOGY_NS}activityStartDate"
    END_DATE_PROPERTY = f"{ONTOLOGY_NS}activityEndDate"
    STATUS_PROPERTY = f"{ONTOLOGY_NS}activityStatus"
    TYPE_PROPERTY = f"{ONTOLOGY_NS}activityType"
    HAS_INSTRUCTOR_PROPERTY = f"{ALT_ONTOLOGY_NS}hasInstructor"
    # Person property for PersonSPARQLService
    PERSON_NAME_PROPERTY = f"{ONTOLOGY_NS}personName"
    
    def __init__(self, endpoint: str = "http://localhost:3030/trelix/sparql"):
        self.endpoint = endpoint
        self.sparql = SPARQLWrapper(endpoint)
        self.sparql.setReturnFormat(JSON)
        update_endpoint = endpoint.replace('/sparql', '/update')
        self.sparql_update = SPARQLWrapper(update_endpoint)
        self.sparql_update.setMethod(POST)
    
    def _execute_query(self, query: str, method: str = "GET") -> Dict:
        self.sparql.setMethod(method)
        self.sparql.setQuery(query)
        try:
            results = self.sparql.query().convert()
            return results
        except Exception as e:
            print(f"SPARQL Query Error: {e}")
            return {"results": {"bindings": []}}
    
    def _execute_update(self, update_query: str) -> bool:
        try:
            self.sparql_update.setQuery(update_query)
            self.sparql_update.query()
            return True
        except Exception as e:
            print(f"SPARQL Update Error: {e}")
            return False
    
    def get_all_activities(self, status: str = None, search: str = None) -> List[Dict]:
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ont: <{self.ONTOLOGY_NS}>
        PREFIX alt: <{self.ALT_ONTOLOGY_NS}>
        
        SELECT ?uri ?name ?description ?duration ?startDate ?endDate ?status ?type ?instructor ?instructorName
        WHERE {{
            ?uri rdf:type <{self.ACTIVITY_CLASS}> .
            OPTIONAL {{ ?uri <{self.ACTIVITY_NAME_PROPERTY}> ?name . }}
            OPTIONAL {{ ?uri <{self.DESCRIPTION_PROPERTY}> ?description . }}
            OPTIONAL {{ ?uri <{self.DURATION_PROPERTY}> ?duration . }}
            OPTIONAL {{ ?uri <{self.START_DATE_PROPERTY}> ?startDate . }}
            OPTIONAL {{ ?uri <{self.END_DATE_PROPERTY}> ?endDate . }}
            OPTIONAL {{ ?uri <{self.STATUS_PROPERTY}> ?status . }}
            OPTIONAL {{ ?uri <{self.TYPE_PROPERTY}> ?type . }}
            OPTIONAL {{ ?uri <{self.HAS_INSTRUCTOR_PROPERTY}> ?instructor . }}
            OPTIONAL {{ ?instructor <{self.PERSON_NAME_PROPERTY}> ?instructorName . }}
        """
        
        # Add status filter in SPARQL
        if status:
            escaped_status = status.replace('"', '\\"').replace('\\', '\\\\')
            query += f'\n            FILTER (STR(?status) = "{escaped_status}") .'
        
        # Add search filter in SPARQL (case-insensitive search in activity name)
        if search:
            escaped_search = search.replace('"', '\\"').replace('\\', '\\\\').replace('*', '\\*')
            query += f'\n            FILTER (CONTAINS(LCASE(STR(?name)), LCASE("{escaped_search}"))) .'
        
        query += """
        }
        ORDER BY ?name
        """
        
        results = self._execute_query(query)
        activities = []
        
        for binding in results.get("results", {}).get("bindings", []):
            duration_value = binding.get("duration", {}).get("value") if binding.get("duration") else None
            activity = {
                "uri": binding.get("uri", {}).get("value", ""),
                "activity_name": binding.get("name", {}).get("value", ""),
                "description": binding.get("description", {}).get("value", "") if binding.get("description") else None,
                "duration": int(duration_value) if duration_value else None,
                "start_date": binding.get("startDate", {}).get("value", "") if binding.get("startDate") else None,
                "end_date": binding.get("endDate", {}).get("value", "") if binding.get("endDate") else None,
                "status": binding.get("status", {}).get("value", "") if binding.get("status") else None,
                "type": binding.get("type", {}).get("value", "") if binding.get("type") else None,
                "instructor_uri": binding.get("instructor", {}).get("value", "") if binding.get("instructor") else None,
                "instructor_name": binding.get("instructorName", {}).get("value", "") if binding.get("instructorName") else None
            }
            activities.append(activity)
        
        return activities
    
    def get_activity_by_uri(self, uri: str) -> Optional[Dict]:
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ont: <{self.ONTOLOGY_NS}>
        PREFIX alt: <{self.ALT_ONTOLOGY_NS}>
        
        SELECT ?name ?description ?duration ?startDate ?endDate ?status ?type ?instructor ?instructorName
        WHERE {{
            <{uri}> rdf:type <{self.ACTIVITY_CLASS}> .
            OPTIONAL {{ <{uri}> <{self.ACTIVITY_NAME_PROPERTY}> ?name . }}
            OPTIONAL {{ <{uri}> <{self.DESCRIPTION_PROPERTY}> ?description . }}
            OPTIONAL {{ <{uri}> <{self.DURATION_PROPERTY}> ?duration . }}
            OPTIONAL {{ <{uri}> <{self.START_DATE_PROPERTY}> ?startDate . }}
            OPTIONAL {{ <{uri}> <{self.END_DATE_PROPERTY}> ?endDate . }}
            OPTIONAL {{ <{uri}> <{self.STATUS_PROPERTY}> ?status . }}
            OPTIONAL {{ <{uri}> <{self.TYPE_PROPERTY}> ?type . }}
            OPTIONAL {{ <{uri}> <{self.HAS_INSTRUCTOR_PROPERTY}> ?instructor . }}
            OPTIONAL {{ ?instructor <{self.PERSON_NAME_PROPERTY}> ?instructorName . }}
        }}
        """
        
        results = self._execute_query(query)
        bindings = results.get("results", {}).get("bindings", [])
        
        if not bindings:
            return None
        
        binding = bindings[0]
        duration_value = binding.get("duration", {}).get("value") if binding.get("duration") else None
        return {
            "uri": uri,
            "activity_name": binding.get("name", {}).get("value", ""),
            "description": binding.get("description", {}).get("value", "") if binding.get("description") else None,
            "duration": int(duration_value) if duration_value else None,
            "start_date": binding.get("startDate", {}).get("value", "") if binding.get("startDate") else None,
            "end_date": binding.get("endDate", {}).get("value", "") if binding.get("endDate") else None,
            "status": binding.get("status", {}).get("value", "") if binding.get("status") else None,
            "type": binding.get("type", {}).get("value", "") if binding.get("type") else None,
            "instructor_uri": binding.get("instructor", {}).get("value", "") if binding.get("instructor") else None,
            "instructor_name": binding.get("instructorName", {}).get("value", "") if binding.get("instructorName") else None
        }
    
    def create_activity(self, activity_name: str, description: str = None, duration: int = None,
                       start_date: str = None, end_date: str = None, status: str = None,
                       activity_type: str = None, instructor_uri: str = None) -> Optional[str]:
        activity_id = activity_name.lower().replace(" ", "_").replace("/", "_").replace("\\", "_")
        activity_id = "".join(c if c.isalnum() or c == "_" else "_" for c in activity_id)[:40]
        activity_id = f"{activity_id}_{int(time.time())}"
        activity_uri = f"{self.ONTOLOGY_NS}{activity_id}"
        
        escaped_name = activity_name.replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
        escaped_desc = description.replace('"', '\\"').replace('\n', '\\n').replace('\r', '') if description else ""
        
        insert_triples = f"""
            <{activity_uri}> rdf:type <{self.ACTIVITY_CLASS}> .
            <{activity_uri}> <{self.ACTIVITY_NAME_PROPERTY}> "{escaped_name}" .
        """
        
        if description:
            insert_triples += f'\n            <{activity_uri}> <{self.DESCRIPTION_PROPERTY}> "{escaped_desc}" .'
        
        if duration is not None:
            insert_triples += f'\n            <{activity_uri}> <{self.DURATION_PROPERTY}> "{duration}"^^<http://www.w3.org/2001/XMLSchema#integer> .'
        
        if start_date:
            insert_triples += f'\n            <{activity_uri}> <{self.START_DATE_PROPERTY}> "{start_date}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .'
        
        if end_date:
            insert_triples += f'\n            <{activity_uri}> <{self.END_DATE_PROPERTY}> "{end_date}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .'
        
        if status:
            escaped_status = status.replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
            insert_triples += f'\n            <{activity_uri}> <{self.STATUS_PROPERTY}> "{escaped_status}" .'
        
        if activity_type:
            escaped_type = activity_type.replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
            insert_triples += f'\n            <{activity_uri}> <{self.TYPE_PROPERTY}> "{escaped_type}" .'
        
        if instructor_uri:
            insert_triples += f'\n            <{activity_uri}> <{self.HAS_INSTRUCTOR_PROPERTY}> <{instructor_uri}> .'
        
        update_query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ont: <{self.ONTOLOGY_NS}>
        
        INSERT DATA {{
            {insert_triples}
        }}
        """
        
        if self._execute_update(update_query):
            return activity_uri
        return None
    
    def update_activity(self, uri: str, activity_name: str = None, description: str = None,
                       duration: int = None, start_date: str = None, end_date: str = None,
                       status: str = None, activity_type: str = None, instructor_uri: str = None) -> bool:
        delete_triples = []
        insert_triples = []
        
        if activity_name:
            escaped_name = activity_name.replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
            delete_triples.append(f'<{uri}> <{self.ACTIVITY_NAME_PROPERTY}> ?oldName .')
            insert_triples.append(f'<{uri}> <{self.ACTIVITY_NAME_PROPERTY}> "{escaped_name}" .')
        
        if description:
            escaped_desc = description.replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
            delete_triples.append(f'<{uri}> <{self.DESCRIPTION_PROPERTY}> ?oldDesc .')
            insert_triples.append(f'<{uri}> <{self.DESCRIPTION_PROPERTY}> "{escaped_desc}" .')
        
        if duration is not None:
            delete_triples.append(f'<{uri}> <{self.DURATION_PROPERTY}> ?oldDuration .')
            insert_triples.append(f'<{uri}> <{self.DURATION_PROPERTY}> "{duration}"^^<http://www.w3.org/2001/XMLSchema#integer> .')
        
        if start_date:
            delete_triples.append(f'<{uri}> <{self.START_DATE_PROPERTY}> ?oldStartDate .')
            insert_triples.append(f'<{uri}> <{self.START_DATE_PROPERTY}> "{start_date}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .')
        
        if end_date:
            delete_triples.append(f'<{uri}> <{self.END_DATE_PROPERTY}> ?oldEndDate .')
            insert_triples.append(f'<{uri}> <{self.END_DATE_PROPERTY}> "{end_date}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .')
        
        if status:
            escaped_status = status.replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
            delete_triples.append(f'<{uri}> <{self.STATUS_PROPERTY}> ?oldStatus .')
            insert_triples.append(f'<{uri}> <{self.STATUS_PROPERTY}> "{escaped_status}" .')
        
        if activity_type:
            escaped_type = activity_type.replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
            delete_triples.append(f'<{uri}> <{self.TYPE_PROPERTY}> ?oldType .')
            insert_triples.append(f'<{uri}> <{self.TYPE_PROPERTY}> "{escaped_type}" .')
        
        if instructor_uri:
            delete_triples.append(f'<{uri}> <{self.HAS_INSTRUCTOR_PROPERTY}> ?oldInstructor .')
            insert_triples.append(f'<{uri}> <{self.HAS_INSTRUCTOR_PROPERTY}> <{instructor_uri}> .')
        
        if not delete_triples:
            return False
        
        delete_clause = " ".join(delete_triples)
        insert_clause = " ".join(insert_triples)
        
        # Build WHERE clause with OPTIONAL to handle cases where properties don't exist
        where_parts = []
        if activity_name is not None:
            where_parts.append(f'OPTIONAL {{ <{uri}> <{self.ACTIVITY_NAME_PROPERTY}> ?oldName . }}')
        if description is not None:
            where_parts.append(f'OPTIONAL {{ <{uri}> <{self.DESCRIPTION_PROPERTY}> ?oldDesc . }}')
        if duration is not None:
            where_parts.append(f'OPTIONAL {{ <{uri}> <{self.DURATION_PROPERTY}> ?oldDuration . }}')
        if start_date is not None:
            where_parts.append(f'OPTIONAL {{ <{uri}> <{self.START_DATE_PROPERTY}> ?oldStartDate . }}')
        if end_date is not None:
            where_parts.append(f'OPTIONAL {{ <{uri}> <{self.END_DATE_PROPERTY}> ?oldEndDate . }}')
        if status is not None:
            where_parts.append(f'OPTIONAL {{ <{uri}> <{self.STATUS_PROPERTY}> ?oldStatus . }}')
        if activity_type is not None:
            where_parts.append(f'OPTIONAL {{ <{uri}> <{self.TYPE_PROPERTY}> ?oldType . }}')
        if instructor_uri is not None:
            where_parts.append(f'OPTIONAL {{ <{uri}> <{self.HAS_INSTRUCTOR_PROPERTY}> ?oldInstructor . }}')
        
        # Ensure WHERE clause always matches by checking if activity exists
        where_clause = f"<{uri}> ?p ?o . " + " . ".join(where_parts) if where_parts else f"<{uri}> ?p ?o ."
        
        update_query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ont: <{self.ONTOLOGY_NS}>
        
        DELETE {{ {delete_clause} }}
        INSERT {{ {insert_clause} }}
        WHERE {{ {where_clause} }}
        """
        
        print(f"Activity update query: {update_query}")  # Debug output
        return self._execute_update(update_query)
    
    def delete_activity(self, uri: str) -> bool:
        update_query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ont: <{self.ONTOLOGY_NS}>
        
        DELETE {{
            <{uri}> ?p ?o .
        }}
        WHERE {{
            <{uri}> ?p ?o .
        }}
        """
        
        return self._execute_update(update_query)