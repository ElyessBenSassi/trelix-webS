from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from trelix_app.utils.sparql_client import run_select, run_update
from datetime import datetime
import json
import uuid
from django.views.decorators.csrf import csrf_exempt
import requests 
import traceback
from huggingface_hub import InferenceClient
from django.conf import settings
import google.generativeai as genai
from django.views.decorators.csrf import csrf_exempt
import os
import re

from openai import OpenAI
HF_API_KEY = "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"
# OpenAI-compatible client pointed at Hugging Face
client = OpenAI(
    api_key=HF_API_KEY,
    base_url="https://api-inference.huggingface.co/v1"   # HF OpenAI endpoint
)
EX = "http://www.semanticweb.org/bazinfo/ontologies/2025/9/untitled-ontology-15#"

def goal_list(request):
    try:
        goals_query = f"""
        PREFIX ex: <{EX}>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT ?goal ?id ?title ?description ?date ?color ?completed
        WHERE {{
          ?goal a ex:Goal .
          OPTIONAL {{ ?goal ex:goalId ?id . }}
          OPTIONAL {{ ?goal ex:goalTitle ?title . }}
          OPTIONAL {{ ?goal ex:goalDescription ?description . }}
          OPTIONAL {{ ?goal ex:goalDate ?date . }}
          OPTIONAL {{ ?goal ex:goalColor ?color . }}
          OPTIONAL {{ ?goal ex:goalCompleted ?completed . }}
        }}
        ORDER BY ?date
        """
        goals_results = run_select(goals_query)
    except Exception as e:
        print(f"[v0] SPARQL goals query error: {e}")
        goals_results = []
    
    goals = []
    for r in goals_results:
        try:
            goal_date = r.get('date', {}).get('value', datetime.now().strftime('%Y-%m-%d'))
            goals.append({
                'id': r.get('id', {}).get('value', str(uuid.uuid4())),
                'uri': r['goal']['value'],
                'title': r.get('title', {}).get('value', 'Untitled Goal'),
                'description': r.get('description', {}).get('value', ''),
                'date': goal_date,
                'color': r.get('color', {}).get('value', '#3b82f6'),
                'completed': r.get('completed', {}).get('value', 'false').lower() == 'true'
            })
        except Exception as e:
            print(f"[v0] Error processing goal: {e}")
            continue
    
    # Fetch events
    try:
        events_query = f"""
        PREFIX ex: <{EX}>
        SELECT ?event ?title ?type ?date ?description ?url
        WHERE {{
          ?event a ex:Event .
          OPTIONAL {{ ?event ex:eventTitle ?title . }}
          OPTIONAL {{ ?event ex:eventType ?type . }}
          OPTIONAL {{ ?event ex:eventDate ?date . }}
          OPTIONAL {{ ?event ex:eventDescription ?description . }}
          OPTIONAL {{ ?event ex:eventUrl ?url . }}
        }}
        ORDER BY ?date
        """
        events_results = run_select(events_query)
    except Exception as e:
        print(f"[v0] SPARQL events query error: {e}")
        events_results = []
    
    events = []
    for r in events_results:
        try:
            events.append({
                'id': str(uuid.uuid4()),
                'uri': r['event']['value'],
                'title': r.get('title', {}).get('value', 'Event'),
                'type': r.get('type', {}).get('value', 'meeting'),
                'date': r.get('date', {}).get('value', datetime.now().strftime('%Y-%m-%d')),
                'description': r.get('description', {}).get('value', ''),
                'url': r.get('url', {}).get('value', '')
            })
        except Exception as e:
            print(f"[v0] Error processing event: {e}")
            continue
    
    context = {
        'goals': goals,
        'events': events,
        'goals_json': json.dumps(goals),
        'events_json': json.dumps(events),
        'current_date': datetime.now().strftime('%Y-%m-%d'),
        'selected_date': datetime.now().strftime('%Y-%m-%d'),
        'is_past_date': False
    }
    return render(request, 'goals/list.html', context)


@require_http_methods(["POST"])
def goal_create(request):
    try:
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        date = request.POST.get('date', datetime.now().strftime('%Y-%m-%d'))
        color = request.POST.get('color', '#3b82f6')
        
        if not title or title.strip() == '':
            return JsonResponse({'success': False, 'error': 'Title is required'}, status=400)
        
        # Escape quotes for SPARQL
        # 🔹 Sanitize function
        def clean_text(text):
            # Remove line breaks
            text = text.replace('\n', ' ').replace('\r', ' ')
            # Keep only alphabetic characters and spaces
            text = re.sub(r'[^a-zA-ZÀ-ÿ\s]', '', text)
            # Collapse multiple spaces
            text = re.sub(r'\s+', ' ', text)
            # Trim extra spaces
            return text.strip()

        title = clean_text(title)
        description = clean_text(description)
        
        goal_id = str(uuid.uuid4())
        new_goal_uri = f"{EX}goal_{goal_id}"
        
        update = f"""
        PREFIX ex: <{EX}>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        INSERT DATA {{
          <{new_goal_uri}> a ex:Goal ;
                           ex:goalId "{goal_id}" ;
                           ex:goalTitle "{title}" ;
                           ex:goalDescription "{description}" ;
                           ex:goalDate "{date}"^^xsd:date ;
                           ex:goalColor "{color}" ;
                           ex:goalCompleted "false" .
        }}
        """
        
        result = run_update(update)
        print(f"[v0] Goal created with ID: {goal_id}, Result: {result}")
        
        return JsonResponse({
            'success': True,
            'goal': {
                'id': goal_id,
                'uri': new_goal_uri,
                'title': title.replace('\\"', '"'),
                'description': description.replace('\\"', '"'),
                'date': date,
                'color': color,
                'completed': False
            }
        })
    except Exception as e:
        print(f"[v0] Error in goal_create: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["DELETE"])
def goal_delete(request, goal_id):
    try:
        query = f"""
        PREFIX ex: <{EX}>
        SELECT ?goal
        WHERE {{
          ?goal ex:goalId "{goal_id}" .
        }}
        """
        results = run_select(query)
        
        if results:
            goal_uri = results[0]['goal']['value']
            update = f"""
            PREFIX ex: <{EX}>
            DELETE WHERE {{
              <{goal_uri}> ?p ?o .
            }}
            """
            run_update(update)
            print(f"[v0] Goal {goal_id} deleted successfully")
            return JsonResponse({'success': True})
        
        print(f"[v0] Goal {goal_id} not found")
        return JsonResponse({'success': False, 'error': 'Goal not found'}, status=404)
    except Exception as e:
        print(f"[v0] Error in goal_delete: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def goal_toggle(request, goal_id):
    try:
        data = json.loads(request.body)
        completed = data.get('completed', False)
        
        query = f"""
        PREFIX ex: <{EX}>
        SELECT ?goal
        WHERE {{
          ?goal ex:goalId "{goal_id}" .
        }}
        """
        results = run_select(query)
        
        if results:
            goal_uri = results[0]['goal']['value']
            completed_str = "true" if completed else "false"
            
            update = f"""
            PREFIX ex: <{EX}>
            DELETE {{
              <{goal_uri}> ex:goalCompleted ?old .
            }}
            INSERT {{
              <{goal_uri}> ex:goalCompleted "{completed_str}" .
            }}
            WHERE {{
              OPTIONAL {{ <{goal_uri}> ex:goalCompleted ?old . }}
            }}
            """
            run_update(update)
            print(f"[v0] Goal {goal_id} toggled to {completed_str}")
            return JsonResponse({'success': True})
        
        print(f"[v0] Goal {goal_id} not found for toggle")
        return JsonResponse({'success': False, 'error': 'Goal not found'}, status=404)
    except Exception as e:
        print(f"[v0] Error in goal_toggle: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def goal_edit(request, goal_title):
    uri = f"{EX}{goal_title.replace(' ', '_')}"
    if request.method == 'POST':
        new_title = request.POST.get('title')
        new_description = request.POST.get('description', '')
        new_date = request.POST.get('date')
        new_color = request.POST.get('color', '#3b82f6')
        
        update = f"""
        PREFIX ex: <{EX}>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        DELETE {{
          <{uri}> ex:goalTitle ?oldTitle .
          <{uri}> ex:goalDescription ?oldDesc .
          <{uri}> ex:goalDate ?oldDate .
          <{uri}> ex:goalColor ?oldColor .
        }}
        INSERT {{
          <{uri}> ex:goalTitle "{new_title}" ;
                  ex:goalDescription "{new_description}" ;
                  ex:goalDate "{new_date}"^^xsd:date ;
                  ex:goalColor "{new_color}" .
        }}
        WHERE {{
          OPTIONAL {{ <{uri}> ex:goalTitle ?oldTitle . }}
          OPTIONAL {{ <{uri}> ex:goalDescription ?oldDesc . }}
          OPTIONAL {{ <{uri}> ex:goalDate ?oldDate . }}
          OPTIONAL {{ <{uri}> ex:goalColor ?oldColor . }}
        }}
        """
        run_update(update)
        return redirect('goal_list')
    return render(request, 'goals/edit.html', {'goal_title': goal_title})


def goals_by_date(request, date):
    """Get all goals for a specific date"""
    query = f"""
    PREFIX ex: <{EX}>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT ?goal ?title ?description ?color ?completed
    WHERE {{
      ?goal a ex:Goal ;
            ex:goalDate "{date}"^^xsd:date .
      OPTIONAL {{ ?goal ex:goalTitle ?title . }}
      OPTIONAL {{ ?goal ex:goalDescription ?description . }}
      OPTIONAL {{ ?goal ex:goalColor ?color . }}
      OPTIONAL {{ ?goal ex:goalCompleted ?completed . }}
    }}
    """
    results = run_select(query)
    goals = [
        {
            'uri': r['goal']['value'],
            'title': r.get('title', {}).get('value', ''),
            'description': r.get('description', {}).get('value', ''),
            'color': r.get('color', {}).get('value', '#3b82f6'),
            'completed': r.get('completed', {}).get('value', 'false').lower() == 'true'
        }
        for r in results
    ]
    return render(request, 'goals/goals_by_date.html', {'goals': goals, 'date': date})


genai.configure(api_key=settings.GOOGLE_API_KEY)

def ai_generate_goal_description(title):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"Generate a short motivational description (4 lines max) for a personal goal titled: '{title}'."
    response = model.generate_content(prompt)
    return response.text.strip()

@csrf_exempt
def generate_goal_description(request):
    print("Gemini Key Loaded:", settings.GOOGLE_API_KEY)

    if request.method == 'POST':
        data = json.loads(request.body)
        title = data.get('title', '')
        if not title:
            return JsonResponse({'error': 'Title is required'}, status=400)
        
        try:
            description = ai_generate_goal_description(title)
            return JsonResponse({'description': description})
        except Exception as e:
            print(f"Gemini error: {e}")
            return JsonResponse({'error': 'AI generation failed'}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=400)