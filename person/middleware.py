from .auth_backend import SPARQLPerson


class SPARQLPersonAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if session has person data
        if 'person_uri' in request.session:
            person_uri = request.session.get('person_uri')
            person_name = request.session.get('person_name', '')
            person_email = request.session.get('person_email', '')
            role_uri = request.session.get('person_role_uri', None)
            role_label = request.session.get('person_role_label', None)
            
            # Attach SPARQL Person as user with role information
            request.user = SPARQLPerson(person_uri, person_name, person_email, role_uri, role_label)
        else:
            # Use AnonymousUser for unauthenticated users
            from django.contrib.auth.models import AnonymousUser
            request.user = AnonymousUser()
        
        response = self.get_response(request)
        return response

