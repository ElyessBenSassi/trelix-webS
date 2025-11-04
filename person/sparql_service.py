from SPARQLWrapper import SPARQLWrapper, JSON, POST
from typing import List, Dict, Optional
import time
import hashlib


class PersonSPARQLService:
    ONTOLOGY_NS = "http://www.semanticweb.org/elyes/ontologies/2025/10/activity-personne-5/"
    # Also support alternative ontology namespace for roles
    ALT_ONTOLOGY_NS = "http://www.semanticweb.org/elyes/ontologies/2025/10/person-activity/"
    PERSON_CLASS = f"{ONTOLOGY_NS}person"
    PERSON_NAME_PROPERTY = f"{ONTOLOGY_NS}personName"
    PERSON_EMAIL_PROPERTY = f"{ONTOLOGY_NS}personEmail"
    PERSON_PASSWORD_PROPERTY = f"{ONTOLOGY_NS}personPassword"
    PERSON_AGE_PROPERTY = f"{ONTOLOGY_NS}personAge"
    PERSON_ROLE_PROPERTY = f"{ONTOLOGY_NS}personRole"
    ROLE_CLASS = f"{ALT_ONTOLOGY_NS}Role"
    
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
    
    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    def sign_up(self, name: str, email: str, password: str, age: int = None, role_uri: str = None) -> Optional[str]:
        existing = self.get_person_by_email(email)
        if existing:
            return None
        
        person_id = email.lower().replace("@", "_at_").replace(".", "_").replace(" ", "_")
        person_id = "".join(c if c.isalnum() or c == "_" else "_" for c in person_id)[:40]
        person_id = f"{person_id}_{int(time.time())}"
        person_uri = f"{self.ONTOLOGY_NS}{person_id}"
        
        hashed_password = self._hash_password(password)
        escaped_name = name.replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
        escaped_email = email.replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
        
        insert_triples = f"""
            <{person_uri}> rdf:type <{self.PERSON_CLASS}> .
            <{person_uri}> <{self.PERSON_NAME_PROPERTY}> "{escaped_name}" .
            <{person_uri}> <{self.PERSON_EMAIL_PROPERTY}> "{escaped_email}" .
            <{person_uri}> <{self.PERSON_PASSWORD_PROPERTY}> "{hashed_password}" .
        """
        
        if age is not None:
            insert_triples += f'\n            <{person_uri}> <{self.PERSON_AGE_PROPERTY}> "{age}"^^<http://www.w3.org/2001/XMLSchema#integer> .'
        
        if role_uri:
            insert_triples += f'\n            <{person_uri}> <{self.PERSON_ROLE_PROPERTY}> <{role_uri}> .'
        
        update_query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ont: <{self.ONTOLOGY_NS}>
        
        INSERT DATA {{
            {insert_triples}
        }}
        """
        
        if self._execute_update(update_query):
            return person_uri
        return None
    
    def sign_in(self, email: str, password: str) -> Optional[Dict]:
        hashed_password = self._hash_password(password)
        
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ont: <{self.ONTOLOGY_NS}>
        
        SELECT ?uri ?name ?email ?age ?role
        WHERE {{
            ?uri rdf:type <{self.PERSON_CLASS}> .
            ?uri <{self.PERSON_EMAIL_PROPERTY}> "{email}" .
            ?uri <{self.PERSON_PASSWORD_PROPERTY}> "{hashed_password}" .
            OPTIONAL {{ ?uri <{self.PERSON_NAME_PROPERTY}> ?name . }}
            OPTIONAL {{ ?uri <{self.PERSON_AGE_PROPERTY}> ?age . }}
            OPTIONAL {{ ?uri <{self.PERSON_ROLE_PROPERTY}> ?role . }}
        }}
        """
        
        results = self._execute_query(query)
        bindings = results.get("results", {}).get("bindings", [])
        
        if not bindings:
            return None
        
        binding = bindings[0]
        age_value = binding.get("age", {}).get("value") if binding.get("age") else None
        return {
            "uri": binding.get("uri", {}).get("value", ""),
            "name": binding.get("name", {}).get("value", ""),
            "email": email,
            "age": int(age_value) if age_value else None,
            "role": binding.get("role", {}).get("value", "") if binding.get("role") else None
        }
    
    def get_person_by_email(self, email: str) -> Optional[Dict]:
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ont: <{self.ONTOLOGY_NS}>
        
        SELECT ?uri ?name ?age ?role
        WHERE {{
            ?uri rdf:type <{self.PERSON_CLASS}> .
            ?uri <{self.PERSON_EMAIL_PROPERTY}> "{email}" .
            OPTIONAL {{ ?uri <{self.PERSON_NAME_PROPERTY}> ?name . }}
            OPTIONAL {{ ?uri <{self.PERSON_AGE_PROPERTY}> ?age . }}
            OPTIONAL {{ ?uri <{self.PERSON_ROLE_PROPERTY}> ?role . }}
        }}
        """
        
        results = self._execute_query(query)
        bindings = results.get("results", {}).get("bindings", [])
        
        if not bindings:
            return None
        
        binding = bindings[0]
        age_value = binding.get("age", {}).get("value") if binding.get("age") else None
        return {
            "uri": binding.get("uri", {}).get("value", ""),
            "name": binding.get("name", {}).get("value", ""),
            "email": email,
            "age": int(age_value) if age_value else None,
            "role": binding.get("role", {}).get("value", "") if binding.get("role") else None
        }
    
    def get_person_by_uri(self, uri: str) -> Optional[Dict]:
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ont: <{self.ONTOLOGY_NS}>
        
        SELECT ?name ?email ?age ?role
        WHERE {{
            <{uri}> rdf:type <{self.PERSON_CLASS}> .
            OPTIONAL {{ <{uri}> <{self.PERSON_NAME_PROPERTY}> ?name . }}
            OPTIONAL {{ <{uri}> <{self.PERSON_EMAIL_PROPERTY}> ?email . }}
            OPTIONAL {{ <{uri}> <{self.PERSON_AGE_PROPERTY}> ?age . }}
            OPTIONAL {{ <{uri}> <{self.PERSON_ROLE_PROPERTY}> ?role . }}
        }}
        """
        
        results = self._execute_query(query)
        bindings = results.get("results", {}).get("bindings", [])
        
        if not bindings:
            return None
        
        binding = bindings[0]
        age_value = binding.get("age", {}).get("value") if binding.get("age") else None
        role = binding.get("role", {}).get("value", "") if binding.get("role") else None
        
        # Extract role label from role URI
        role_label = None
        if role:
            if "#" in role:
                role_label = role.split("#")[-1]
            elif "/" in role:
                role_label = role.split("/")[-1]
            else:
                role_label = role
        
        return {
            "uri": uri,
            "name": binding.get("name", {}).get("value", ""),
            "email": binding.get("email", {}).get("value", ""),
            "age": int(age_value) if age_value else None,
            "role": role,
            "role_uri": role,
            "role_label": role_label
        }
    
    def get_all_persons(self) -> List[Dict]:
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ont: <{self.ONTOLOGY_NS}>
        
        SELECT ?uri ?name ?email ?age ?role
        WHERE {{
            ?uri rdf:type <{self.PERSON_CLASS}> .
            OPTIONAL {{ ?uri <{self.PERSON_NAME_PROPERTY}> ?name . }}
            OPTIONAL {{ ?uri <{self.PERSON_EMAIL_PROPERTY}> ?email . }}
            OPTIONAL {{ ?uri <{self.PERSON_AGE_PROPERTY}> ?age . }}
            OPTIONAL {{ ?uri <{self.PERSON_ROLE_PROPERTY}> ?role . }}
        }}
        ORDER BY ?name
        """
        
        results = self._execute_query(query)
        bindings = results.get("results", {}).get("bindings", [])
        
        persons = []
        for binding in bindings:
            uri = binding.get("uri", {}).get("value", "")
            name = binding.get("name", {}).get("value", "") if binding.get("name") else ""
            email = binding.get("email", {}).get("value", "") if binding.get("email") else ""
            age_value = binding.get("age", {}).get("value") if binding.get("age") else None
            role = binding.get("role", {}).get("value", "") if binding.get("role") else None
            
            # Extract role label from URI if available
            role_label = None
            if role:
                if "#" in role:
                    role_label = role.split("#")[-1]
                elif "/" in role:
                    role_label = role.split("/")[-1]
                else:
                    role_label = role
            
            persons.append({
                "uri": uri,
                "name": name,
                "email": email,
                "age": int(age_value) if age_value else None,
                "role_uri": role,
                "role_label": role_label
            })
        
        return persons
    
    def update_person(self, person_uri: str, name: str = None, email: str = None, 
                     age: int = None, role_uri: str = None) -> bool:
        delete_triples = []
        insert_triples = []
        
        if name is not None:
            escaped_name = name.replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
            delete_triples.append(f'<{person_uri}> <{self.PERSON_NAME_PROPERTY}> ?oldName .')
            insert_triples.append(f'<{person_uri}> <{self.PERSON_NAME_PROPERTY}> "{escaped_name}" .')
        
        if email is not None:
            escaped_email = email.replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
            delete_triples.append(f'<{person_uri}> <{self.PERSON_EMAIL_PROPERTY}> ?oldEmail .')
            insert_triples.append(f'<{person_uri}> <{self.PERSON_EMAIL_PROPERTY}> "{escaped_email}" .')
        
        if age is not None:
            delete_triples.append(f'<{person_uri}> <{self.PERSON_AGE_PROPERTY}> ?oldAge .')
            insert_triples.append(f'<{person_uri}> <{self.PERSON_AGE_PROPERTY}> "{age}"^^<http://www.w3.org/2001/XMLSchema#integer> .')
        
        if role_uri is not None:
            delete_triples.append(f'<{person_uri}> <{self.PERSON_ROLE_PROPERTY}> ?oldRole .')
            if role_uri:  # If role_uri is not empty, add it
                insert_triples.append(f'<{person_uri}> <{self.PERSON_ROLE_PROPERTY}> <{role_uri}> .')
            # If role_uri is empty, we just delete the old role
        
        if not delete_triples:
            return False
        
        # Join triples - each already ends with '.', so join with space
        delete_clause = " ".join(delete_triples)
        insert_clause = " ".join(insert_triples) if insert_triples else ""
        
        if insert_clause:
            update_query = f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX ont: <{self.ONTOLOGY_NS}>
            
            DELETE {{ {delete_clause} }}
            INSERT {{ {insert_clause} }}
            WHERE {{ {delete_clause} }}
            """
        else:
            # Only delete, no insert
            update_query = f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX ont: <{self.ONTOLOGY_NS}>
            
            DELETE {{ {delete_clause} }}
            WHERE {{ {delete_clause} }}
            """
        
        # Build WHERE clause with OPTIONAL to handle cases where properties don't exist
        where_parts = []
        if name is not None:
            where_parts.append(f'OPTIONAL {{ <{person_uri}> <{self.PERSON_NAME_PROPERTY}> ?oldName . }}')
        if email is not None:
            where_parts.append(f'OPTIONAL {{ <{person_uri}> <{self.PERSON_EMAIL_PROPERTY}> ?oldEmail . }}')
        if age is not None:
            where_parts.append(f'OPTIONAL {{ <{person_uri}> <{self.PERSON_AGE_PROPERTY}> ?oldAge . }}')
        if role_uri is not None:
            where_parts.append(f'OPTIONAL {{ <{person_uri}> <{self.PERSON_ROLE_PROPERTY}> ?oldRole . }}')
        
        # Ensure WHERE clause always matches by checking if person exists
        where_clause = f"<{person_uri}> ?p ?o . " + " . ".join(where_parts) if where_parts else f"<{person_uri}> ?p ?o ."
        
        # Rebuild update query with proper WHERE clause
        if insert_clause:
            update_query = f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22/rdf-syntax-ns#>
            PREFIX ont: <{self.ONTOLOGY_NS}>
            
            DELETE {{ {delete_clause} }}
            INSERT {{ {insert_clause} }}
            WHERE {{ {where_clause} }}
            """
        else:
            update_query = f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22/rdf-syntax-ns#>
            PREFIX ont: <{self.ONTOLOGY_NS}>
            
            DELETE {{ {delete_clause} }}
            WHERE {{ {where_clause} }}
            """
        
        print(f"Update query: {update_query}")  # Debug output
        return self._execute_update(update_query)
    
    def delete_person(self, person_uri: str) -> bool:
        update_query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ont: <{self.ONTOLOGY_NS}>
        
        DELETE {{
            <{person_uri}> ?p ?o .
        }}
        WHERE {{
            <{person_uri}> ?p ?o .
        }}
        """
        
        return self._execute_update(update_query)
    
    def get_available_roles(self, exclude_administrator: bool = False) -> List[Dict[str, str]]:
        """
        Get all available roles from the ontology.
        
        Args:
            exclude_administrator: If True, exclude Administrator role from results
        """
        role_base_alt = self.ALT_ONTOLOGY_NS.rstrip('/').rstrip('#')
        role_class_alt_hash = f"{role_base_alt}#Role"
        role_class_alt_slash = f"{self.ALT_ONTOLOGY_NS}Role"
        
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        
        SELECT DISTINCT ?role ?label
        WHERE {{
            {{
                ?role rdf:type <{self.ONTOLOGY_NS}Role> .
                OPTIONAL {{ ?role rdfs:label ?label . }}
            }}
            UNION
            {{
                ?role rdf:type <{role_class_alt_hash}> .
                OPTIONAL {{ ?role rdfs:label ?label . }}
            }}
            UNION
            {{
                ?role rdf:type <{role_class_alt_slash}> .
                OPTIONAL {{ ?role rdfs:label ?label . }}
            }}
            UNION
            {{
                ?role rdf:type owl:NamedIndividual .
                ?role rdf:type <{role_class_alt_hash}> .
                OPTIONAL {{ ?role rdfs:label ?label . }}
            }}
        }}
        ORDER BY ?label
        """
        
        results = self._execute_query(query)
        bindings = results.get("results", {}).get("bindings", [])
        
        # Debug: Print query results
        print(f"Role query returned {len(bindings)} bindings")
        if bindings:
            print(f"First binding: {bindings[0]}")
        
        roles = []
        for binding in bindings:
            role_uri = binding.get("role", {}).get("value", "")
            label = binding.get("label", {}).get("value", "")
            
            if not label and role_uri:
                if "#" in role_uri:
                    label = role_uri.split("#")[-1]
                elif "/" in role_uri:
                    label = role_uri.split("/")[-1]
                else:
                    label = role_uri
            
            if role_uri:
                # Exclude Administrator if requested
                if exclude_administrator:
                    role_str = (label or role_uri).lower()
                    if "administrator" in role_str:
                        continue
                
                roles.append({
                    "uri": role_uri,
                    "label": label or role_uri
                })
        
        if not roles:
            print("No roles found with general query, trying specific role URIs...")
            role_base = self.ALT_ONTOLOGY_NS.rstrip('/').rstrip('#')
            known_roles = [
                {"uri": f"{role_base}#Student", "label": "Student"},
                {"uri": f"{role_base}#Instructor", "label": "Instructor"},
                {"uri": f"{role_base}#Administrator", "label": "Administrator"},
            ]
            
            for role in known_roles:
                # Exclude Administrator if requested
                if exclude_administrator and role["label"] == "Administrator":
                    continue
                    
                verify_query = f"""
                PREFIX rdf: <http://www.w3.org/1999/02/22/rdf-syntax-ns#>
                
                ASK {{
                    <{role['uri']}> ?p ?o .
                }}
                """
                try:
                    verify_results = self._execute_query(verify_query)
                    if verify_results.get("boolean", False):
                        roles.append(role)
                except:
                    pass
        
        return roles
