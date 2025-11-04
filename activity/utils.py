import google.generativeai as genai
from django.conf import settings
from .sparql_service import ActivitySPARQLService
import json
from typing import List, Dict

class ActivityTipsSuggestions:
    def __init__(self, api_key: str = None, model_name: str = None):
        self.api_key = api_key or getattr(settings, 'GOOGLE_API_KEY', None)
        if not self.api_key:
            raise ValueError("Google API key not found. Please set GOOGLE_API_KEY in settings or .env file.")
        
        genai.configure(api_key=self.api_key)
        
        configured_model = (
            model_name
            or getattr(settings, 'GEMINI_MODEL_NAME', None)
            or 'models/gemini-2.5-flash-lite'
        )

        normalized_model = configured_model.replace('models/', '', 1) if configured_model.startswith('models/') else configured_model

        try:
            self.model = genai.GenerativeModel(normalized_model)
        except Exception as e:
            raise ValueError(
                f"Failed to initialize Gemini model. Configured='{configured_model}', used='{normalized_model}'. Error: {str(e)}"
            )
    
    def get_tips(self, activity_name: str, activity_description: str) -> List[Dict]:
        description_text = activity_description if activity_description else "No description provided"
        prompt = f"""You are a helpful assistant that generates tips for an activity.

Activity Name: {activity_name}
Activity Description: {description_text}

Generate exactly 3 helpful and relevant tips for this activity. The tips should be practical, actionable, and specific to the activity.

Return ONLY a valid JSON array in this exact format (no markdown, no code blocks, no explanations):
[
    {{
        "tip": "First practical tip here"
    }},
    {{
        "tip": "Second practical tip here"
    }},
    {{
        "tip": "Third practical tip here"
    }}
]"""
        try:
            response = self.model.generate_content(prompt)
            raw_text = response.text
            # Clean the response text
            clean_text = raw_text.strip()
            # Remove markdown code blocks if present
            if clean_text.startswith("```"):
                clean_text = clean_text.split("```")[1]
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:]
            clean_text = clean_text.strip()
            # Parse JSON
            tips = json.loads(clean_text)
            # Ensure it's a list and has the expected structure
            if not isinstance(tips, list):
                raise ValueError("Response is not a list")
            # Validate structure
            for tip in tips:
                if not isinstance(tip, dict) or "tip" not in tip:
                    raise ValueError("Invalid tip structure")
            return tips[:3]  # Ensure maximum 3 tips
        except json.JSONDecodeError as e:
            print(f"JSON decode error in get_tips: {e}")
            print(f"Raw response: {raw_text}")
            return []
        except Exception as e:
            print(f"Error generating tips: {e}")
            return []

    @staticmethod
    def get_activity_content(activity_uri: str) -> Dict:
        return ActivitySPARQLService().get_activity_by_uri(activity_uri)

    @staticmethod
    def get_activities() -> List[Dict]:
        return ActivitySPARQLService().get_all_activities()

    def generate_suggestions(self, activity_uri: str) -> List[Dict]:
        activity_content = ActivityTipsSuggestions.get_activity_content(activity_uri)
        activities = ActivityTipsSuggestions.get_activities()
        
        if not activity_content:
            return []
        
        # Filter out the current activity from the list
        available_activities = [a for a in activities if a.get("uri") != activity_uri]
        
        if not available_activities:
            return []
        
        # Prepare activity information for the prompt
        current_activity_info = f"""
Current Activity:
- Name: {activity_content.get('activity_name', 'N/A')}
- Description: {activity_content.get('description', 'No description')}
- Type: {activity_content.get('type', 'N/A')}
- Status: {activity_content.get('status', 'N/A')}
"""
        
        # Prepare available activities list
        activities_list = ""
        for idx, act in enumerate(available_activities[:20], 1):  # Limit to 20 for prompt size
            activities_list += f"\n{idx}. Name: {act.get('activity_name', 'N/A')}\n"
            activities_list += f"   Description: {act.get('description', 'No description')}\n"
            activities_list += f"   Type: {act.get('type', 'N/A')}\n"
            activities_list += f"   URI: {act.get('uri', '')}\n"
        
        prompt = f"""You are a helpful assistant that suggests similar activities based on a current activity.

{current_activity_info}

Available Activities:
{activities_list}

Analyze the current activity and find the 3 most similar activities from the available list. Consider factors like:
- Activity type/category
- Description similarity
- Purpose and goals
- Target audience

Return ONLY a valid JSON array in this exact format (no markdown, no code blocks, no explanations):
[
    {{
        "uri": "exact_uri_from_available_activities",
        "activity_name": "exact_name_from_available_activities",
        "description": "exact_or_summarized_description"
    }},
    {{
        "uri": "exact_uri_from_available_activities",
        "activity_name": "exact_name_from_available_activities",
        "description": "exact_or_summarized_description"
    }},
    {{
        "uri": "exact_uri_from_available_activities",
        "activity_name": "exact_name_from_available_activities",
        "description": "exact_or_summarized_description"
    }}
]

IMPORTANT: 
- Return exactly 3 suggestions (or fewer if less than 3 similar activities are available)
- Use the exact URIs from the available activities list
- Use the exact activity names from the available activities list
- Descriptions can be the original or a brief summary"""
        
        try:
            response = self.model.generate_content(prompt)
            raw_text = response.text
            # Clean the response text
            clean_text = raw_text.strip()
            # Remove markdown code blocks if present
            if clean_text.startswith("```"):
                clean_text = clean_text.split("```")[1]
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:]
            clean_text = clean_text.strip()
            # Parse JSON
            suggestions = json.loads(clean_text)
            # Ensure it's a list
            if not isinstance(suggestions, list):
                raise ValueError("Response is not a list")
            # Validate structure and verify URIs exist in available activities
            valid_suggestions = []
            available_uris = {act.get("uri") for act in available_activities}
            for suggestion in suggestions:
                if not isinstance(suggestion, dict):
                    continue
                uri = suggestion.get("uri")
                if uri and uri in available_uris:
                    # Find the original activity to get full details
                    original_act = next((a for a in available_activities if a.get("uri") == uri), None)
                    if original_act:
                        valid_suggestions.append({
                            "uri": uri,
                            "activity_name": original_act.get("activity_name", ""),
                            "description": original_act.get("description", "")
                        })
            # Limit to 3 suggestions
            return valid_suggestions[:3]
        except json.JSONDecodeError as e:
            print(f"JSON decode error in generate_suggestions: {e}")
            print(f"Raw response: {raw_text}")
            return []
        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return []