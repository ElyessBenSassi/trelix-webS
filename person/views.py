from django.shortcuts import render, redirect
from django.contrib import messages
from functools import wraps
from .sparql_service import PersonSPARQLService
from .models import Person


def administrator_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to access this page.')
            return redirect('person:sign_in')
        
        # Check if user has Administrator role
        if not request.user.is_administrator():
            messages.error(request, 'Access denied. Administrator role required.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def sign_up(request):
    # Redirect authenticated users to home
    if request.user.is_authenticated:
        messages.info(request, 'You are already signed in.')
        return redirect('home')
    
    sparql_service = PersonSPARQLService()
    # Exclude Administrator role from signup
    available_roles = sparql_service.get_available_roles(exclude_administrator=True)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        age_raw = request.POST.get('age', '').strip() or None
        role_uri = request.POST.get('role', '').strip() or None
        
        if not name or not email or not password:
            messages.error(request, 'Name, email and password are required.')
            return render(request, 'person/signup.html', {'roles': available_roles})
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'person/signup.html', {'roles': available_roles})
        
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return render(request, 'person/signup.html', {'roles': available_roles})
        
        age = int(age_raw) if age_raw and age_raw.isdigit() else None
        
        # Create SPARQL Person
        person_uri = sparql_service.sign_up(name, email, password, age, role_uri)
        
        if person_uri:
            messages.success(request, f'Account created successfully! Welcome, {name}!')
            # Set session data for authentication
            request.session['person_uri'] = person_uri
            request.session['user_uri'] = person_uri  # ✅ ajout
            request.session['person_name'] = name
            request.session['person_email'] = email
            
            # Store role information if provided
            if role_uri:
                role_label = None
                if "#" in role_uri:
                    role_label = role_uri.split("#")[-1]
                elif "/" in role_uri:
                    role_label = role_uri.split("/")[-1]
                request.session['person_role_uri'] = role_uri
                request.session['person_role_label'] = role_label
            
            return redirect('home')
        else:
            messages.error(request, 'Account creation failed. Email may already be in use.')
            return render(request, 'person/signup.html', {'roles': available_roles})
    
    return render(request, 'person/signup.html', {'roles': available_roles})


def sign_in(request):
    # Redirect authenticated users to home
    if request.user.is_authenticated:
        messages.info(request, 'You are already signed in.')
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not email or not password:
            messages.error(request, 'Email and password are required.')
            return render(request, 'person/signin.html')
        
        # SPARQL authentication
        sparql_service = PersonSPARQLService()
        person_data = sparql_service.sign_in(email, password)
        
        if person_data:
            request.session['person_uri'] = person_data['uri']
            request.session['user_uri'] = person_data['uri']  # ✅ pour le système des événements

            request.session['person_name'] = person_data['name']
            request.session['person_email'] = person_data['email']
            
            # Store role information
            role_uri = person_data.get('role')
            role_label = None
            if role_uri:
                # Extract role label from URI
                if "#" in role_uri:
                    role_label = role_uri.split("#")[-1]
                elif "/" in role_uri:
                    role_label = role_uri.split("/")[-1]
            
            request.session['person_role_uri'] = role_uri
            request.session['person_role_label'] = role_label
            
            messages.success(request, f'Welcome back, {person_data["name"]}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'person/signin.html')
    
    return render(request, 'person/signin.html')


def sign_out(request):
    request.session.flush()
    messages.success(request, 'You have been signed out successfully.')
    return redirect('home')


@administrator_required
def admin_persons(request):
    sparql_service = PersonSPARQLService()
    persons_data = sparql_service.get_all_persons()
    
    # Convert to Person objects for consistency
    persons = []
    for person_data in persons_data:
        person = Person.from_dict(person_data)
        persons.append(person)
    
    # Get available roles for edit form
    available_roles = sparql_service.get_available_roles()
    
    context = {
        'persons': persons,
        'total_count': len(persons),
        'available_roles': available_roles
    }
    
    return render(request, 'person/admin_persons.html', context)


@administrator_required
def admin_person_edit(request, person_uri):
    from urllib.parse import unquote
    
    person_uri_decoded = unquote(person_uri)
    sparql_service = PersonSPARQLService()
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        age_raw = request.POST.get('age', '').strip() or None
        role_uri = request.POST.get('role', '').strip() or None
        
        if not name or not email:
            messages.error(request, 'Name and email are required.')
            person_data = sparql_service.get_person_by_uri(person_uri_decoded)
            if not person_data:
                messages.error(request, 'Person not found.')
                return redirect('person:admin_persons')
            person = Person.from_dict(person_data)
            available_roles = sparql_service.get_available_roles()
            is_administrator = person.role_label and "administrator" in person.role_label.lower()
            return render(request, 'person/admin_person_edit.html', {
                'person': person,
                'available_roles': available_roles,
                'is_administrator': is_administrator
            })
        
        # Get current person data to check if they're an Administrator
        current_person_data = sparql_service.get_person_by_uri(person_uri_decoded)
        is_administrator = False
        if current_person_data:
            current_person = Person.from_dict(current_person_data)
            # Check both role_label and role_uri for administrator
            if current_person.role_label:
                is_administrator = "administrator" in current_person.role_label.lower()
            elif current_person.role_uri:
                is_administrator = "administrator" in current_person.role_uri.lower()
            elif current_person.role:
                is_administrator = "administrator" in current_person.role.lower()
            
            # If person is Administrator, preserve the role (don't update it)
            if is_administrator:
                # Set role_uri to None so update_person won't touch the role property
                role_uri = None
            else:
                # For non-administrators, prevent role changes if they somehow try to change to admin
                preserve_role = request.POST.get('preserve_role', '').strip()
                if preserve_role == 'true':
                    role_uri = None
        
        age = int(age_raw) if age_raw and age_raw.isdigit() else None
        
        # Update person - if role_uri is None, the role property won't be touched
        success = sparql_service.update_person(person_uri_decoded, name, email, age, role_uri)
        
        if success:
            # If editing the current user, update session role information
            if request.user.uri == person_uri_decoded:
                role_label = None
                if role_uri:
                    if "#" in role_uri:
                        role_label = role_uri.split("#")[-1]
                    elif "/" in role_uri:
                        role_label = role_uri.split("/")[-1]
                request.session['person_role_uri'] = role_uri
                request.session['person_role_label'] = role_label
                # Update the user object
                request.user.role_uri = role_uri
                request.user.role_label = role_label
            
            messages.success(request, f'Person "{name}" updated successfully!')
            return redirect('person:admin_persons')
        else:
            messages.error(request, 'Failed to update person. Please try again.')
    
    # GET request - show edit form
    person_data = sparql_service.get_person_by_uri(person_uri_decoded)
    
    if not person_data:
        messages.error(request, 'Person not found.')
        return redirect('person:admin_persons')
    
    person = Person.from_dict(person_data)
    available_roles = sparql_service.get_available_roles()
    
    # Check if person is currently an Administrator
    # Check both role_label and role_uri for administrator
    is_administrator = False
    if person.role_label:
        is_administrator = "administrator" in person.role_label.lower()
    elif person.role_uri:
        is_administrator = "administrator" in person.role_uri.lower()
    elif person.role:
        is_administrator = "administrator" in person.role.lower()
    
    context = {
        'person': person,
        'available_roles': available_roles,
        'is_administrator': is_administrator
    }
    
    return render(request, 'person/admin_person_edit.html', context)


@administrator_required
def admin_person_delete(request, person_uri):
    from urllib.parse import unquote
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('person:admin_persons')
    
    person_uri_decoded = unquote(person_uri)
    sparql_service = PersonSPARQLService()
    
    # Get person info before deletion for message
    person_data = sparql_service.get_person_by_uri(person_uri_decoded)
    
    if not person_data:
        messages.error(request, 'Person not found.')
        return redirect('person:admin_persons')
    
    person = Person.from_dict(person_data)
    person_name = person.name
    
    # Prevent administrators from deleting themselves
    if request.user.uri == person_uri_decoded:
        messages.error(request, 'You cannot delete yourself.')
        return redirect('person:admin_persons')
    
    success = sparql_service.delete_person(person_uri_decoded)
    
    if success:
        messages.success(request, f'Person "{person_name}" deleted successfully!')
    else:
        messages.error(request, 'Failed to delete person. Please try again.')
    
    return redirect('person:admin_persons')
