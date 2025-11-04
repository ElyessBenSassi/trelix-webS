from django.shortcuts import render, redirect
from django.contrib import messages
from .sparql_service import ActivitySPARQLService
from .models import Activity


def activity_list(request):
    sparql_service = ActivitySPARQLService()
    
    # Get filter parameters from query string
    status_filter = request.GET.get('status', '').strip()
    search_query = request.GET.get('search', '').strip()
    
    # Get activities with SPARQL filtering
    activities_data = sparql_service.get_all_activities(status=status_filter if status_filter else None, 
                                                         search=search_query if search_query else None)
    activities = [Activity.from_dict(activity_data) for activity_data in activities_data]
    
    context = {
        'activities': activities,
        'status_filter': status_filter,
        'search_query': search_query,
        'has_filters': bool(status_filter or search_query)
    }
    
    return render(request, 'activity/index.html', context)


def activity_detail(request, activity_uri):
    from urllib.parse import unquote
    sparql_service = ActivitySPARQLService()
    # Decode the URI if it was URL-encoded
    activity_uri_decoded = unquote(activity_uri)
    activity_data = sparql_service.get_activity_by_uri(activity_uri_decoded)
    
    if not activity_data:
        messages.error(request, 'Activity not found.')
        return redirect('activity:activity_list')
    
    activity = Activity.from_dict(activity_data)
    
    context = {
        'activity': activity
    }
    
    return render(request, 'activity/detail.html', context)


def activity_create(request):
    if not request.user.is_authenticated:
        messages.error(request, 'You must be logged in to create an activity.')
        return redirect('person:sign_in')
    
    # Check if user has Administrator or Instructor role
    if not request.user.can_create_activity():
        messages.error(request, 'Access denied. Only Administrators and Instructors can create activities.')
        return redirect('activity:activity_list')
    
    if request.method == 'POST':
        activity_name = request.POST.get('activity_name', '').strip()
        description = request.POST.get('description', '').strip() or None
        duration_raw = request.POST.get('duration', '').strip() or None
        start_date_raw = request.POST.get('start_date', '').strip() or None
        end_date_raw = request.POST.get('end_date', '').strip() or None
        status = request.POST.get('status', '').strip() or None
        activity_type = request.POST.get('type', '').strip() or None
        
        if not activity_name:
            messages.error(request, 'Activity name is required.')
            return render(request, 'activity/create.html')
        
        duration = int(duration_raw) if duration_raw and duration_raw.isdigit() else None
        
        start_date = None
        if start_date_raw:
            if len(start_date_raw) == 16:
                start_date = start_date_raw + ':00'
            else:
                start_date = start_date_raw
        
        end_date = None
        if end_date_raw:
            if len(end_date_raw) == 16:
                end_date = end_date_raw + ':00'
            else:
                end_date = end_date_raw
        
        # Use authenticated user's person_uri as instructor
        instructor_uri = request.session.get('person_uri')
        
        sparql_service = ActivitySPARQLService()
        activity_uri = sparql_service.create_activity(
            activity_name, description, duration, start_date, end_date, status, activity_type, instructor_uri
        )
        
        if activity_uri:
            messages.success(request, f'Activity "{activity_name}" created successfully!')
            return redirect('activity:activity_list')
        else:
            messages.error(request, 'Failed to create activity. Please try again.')
            return render(request, 'activity/create.html')
    
    return render(request, 'activity/create.html')


def activity_delete(request, activity_uri):
    from urllib.parse import unquote
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('activity:activity_list')
    
    if not request.user.is_authenticated:
        messages.error(request, 'You must be logged in to delete an activity.')
        return redirect('person:sign_in')
    
    activity_uri_decoded = unquote(activity_uri)
    sparql_service = ActivitySPARQLService()
    
    # Get activity to check ownership
    activity_data = sparql_service.get_activity_by_uri(activity_uri_decoded)
    
    if not activity_data:
        messages.error(request, 'Activity not found.')
        return redirect('activity:activity_list')
    
    activity = Activity.from_dict(activity_data)
    
    # Check if user is the owner (instructor) or Administrator
    is_owner = activity.instructor_uri == request.user.uri if activity.instructor_uri else False
    is_admin = request.user.is_administrator()
    
    if not (is_owner or is_admin):
        messages.error(request, 'Access denied. Only the activity owner or Administrator can delete activities.')
        return redirect('activity:activity_list')
    
    activity_name = activity.activity_name
    success = sparql_service.delete_activity(activity_uri_decoded)
    
    if success:
        messages.success(request, f'Activity "{activity_name}" deleted successfully!')
    else:
        messages.error(request, 'Failed to delete activity. Please try again.')
    
    return redirect('activity:activity_list')


def activity_edit(request, activity_uri):
    from urllib.parse import unquote
    
    if not request.user.is_authenticated:
        messages.error(request, 'You must be logged in to edit an activity.')
        return redirect('person:sign_in')
    
    activity_uri_decoded = unquote(activity_uri)
    sparql_service = ActivitySPARQLService()
    
    # Get activity to check ownership
    activity_data = sparql_service.get_activity_by_uri(activity_uri_decoded)
    
    if not activity_data:
        messages.error(request, 'Activity not found.')
        return redirect('activity:activity_list')
    
    activity = Activity.from_dict(activity_data)
    
    # Check if user is the owner (instructor) or Administrator
    is_owner = activity.instructor_uri == request.user.uri if activity.instructor_uri else False
    is_admin = request.user.is_administrator()
    
    if not (is_owner or is_admin):
        messages.error(request, 'Access denied. Only the activity owner or Administrator can edit activities.')
        return redirect('activity:activity_list')
    
    if request.method == 'POST':
        activity_name = request.POST.get('activity_name', '').strip()
        description = request.POST.get('description', '').strip() or None
        duration_raw = request.POST.get('duration', '').strip() or None
        start_date_raw = request.POST.get('start_date', '').strip() or None
        end_date_raw = request.POST.get('end_date', '').strip() or None
        status = request.POST.get('status', '').strip() or None
        activity_type = request.POST.get('type', '').strip() or None
        
        if not activity_name:
            messages.error(request, 'Activity name is required.')
            return render(request, 'activity/edit.html', {'activity': activity, 'is_admin': is_admin})
        
        duration = int(duration_raw) if duration_raw and duration_raw.isdigit() else None
        
        start_date = None
        if start_date_raw:
            if len(start_date_raw) == 16:
                start_date = start_date_raw + ':00'
            else:
                start_date = start_date_raw
        
        end_date = None
        if end_date_raw:
            if len(end_date_raw) == 16:
                end_date = end_date_raw + ':00'
            else:
                end_date = end_date_raw
        
        # Only allow changing instructor if user is Administrator
        instructor_uri = activity.instructor_uri
        if is_admin:
            instructor_uri_raw = request.POST.get('instructor_uri', '').strip() or None
            instructor_uri = instructor_uri_raw if instructor_uri_raw else activity.instructor_uri
        
        success = sparql_service.update_activity(
            activity_uri_decoded, activity_name, description, duration, 
            start_date, end_date, status, activity_type, instructor_uri
        )
        
        if success:
            messages.success(request, f'Activity "{activity_name}" updated successfully!')
            return redirect('activity:activity_detail', activity_uri=activity_uri)
        else:
            messages.error(request, 'Failed to update activity. Please try again.')
            return render(request, 'activity/edit.html', {'activity': activity, 'is_admin': is_admin})
    
    # GET request - show edit form
    context = {
        'activity': activity,
        'is_admin': is_admin
    }
    
    return render(request, 'activity/edit.html', context)
