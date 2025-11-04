import os
import sys
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trelix_app.settings')

# Initialize Django
import django
django.setup()

# Now import Django modules
from activity.sparql_service import ActivitySPARQLService
from person.sparql_service import PersonSPARQLService

# SPARQL endpoint configuration
FUSEKI_ENDPOINT = "http://localhost:3030/trelix/sparql"

# Instructor configuration
INSTRUCTOR_EMAIL = "trelix@trelix.com"
INSTRUCTOR_NAME = "trelix"
INSTRUCTOR_PASSWORD = "trelix"
INSTRUCTOR_ROLE_URI = "http://www.semanticweb.org/elyes/ontologies/2025/10/person-activity/#Instructor"


def check_if_data_exists():
    """Check if initial data already exists in the database."""
    print("Checking if initial data already exists...")
    
    # Check if instructor exists
    person_service = PersonSPARQLService(FUSEKI_ENDPOINT)
    existing_person = person_service.get_person_by_email(INSTRUCTOR_EMAIL)
    
    if existing_person:
        print(f"✓ Instructor '{INSTRUCTOR_NAME}' already exists with URI: {existing_person.get('uri')}")
        return True
    
    # Check if any activities exist (optional check)
    activity_service = ActivitySPARQLService(FUSEKI_ENDPOINT)
    existing_activities = activity_service.get_all_activities()
    
    if existing_activities:
        print(f"✓ Found {len(existing_activities)} existing activities in the database")
        # Still return False if instructor doesn't exist, as we need to create it
        return False
    
    print("No initial data found. Proceeding with seed...")
    return False


def create_instructor():
    """Create the instructor user in the database."""
    print(f"\nCreating instructor: {INSTRUCTOR_NAME} ({INSTRUCTOR_EMAIL})...")
    
    person_service = PersonSPARQLService(FUSEKI_ENDPOINT)
    
    # Check if instructor already exists
    existing_person = person_service.get_person_by_email(INSTRUCTOR_EMAIL)
    if existing_person:
        print(f"  ✓ Instructor already exists with URI: {existing_person.get('uri')}")
        return existing_person.get('uri')
    
    # Get Instructor role URI if not already set
    # Try to get available roles first
    roles = person_service.get_available_roles()
    instructor_role_uri = None
    
    for role in roles:
        if "instructor" in role.get("label", "").lower():
            instructor_role_uri = role.get("uri")
            break
    
    # If no role found, use the default
    if not instructor_role_uri:
        instructor_role_uri = INSTRUCTOR_ROLE_URI
        print(f"  ⚠ Using default Instructor role URI: {instructor_role_uri}")
    
    # Create the instructor
    person_uri = person_service.sign_up(
        name=INSTRUCTOR_NAME,
        email=INSTRUCTOR_EMAIL,
        password=INSTRUCTOR_PASSWORD,
        age=None,
        role_uri=instructor_role_uri
    )
    
    if person_uri:
        print(f"  ✓ Instructor created successfully with URI: {person_uri}")
        return person_uri
    else:
        print(f"  ✗ Failed to create instructor")
        return None


def create_activities(instructor_uri: str):
    """Create sample activities assigned to the instructor."""
    print(f"\nCreating sample activities for instructor: {instructor_uri}...")
    
    activity_service = ActivitySPARQLService(FUSEKI_ENDPOINT)
    
    # Define sample activities
    activities_data = [
    {
        "activity_name": "Angular Routing Task",
        "description": "Implement complex nested routes and lazy loading modules in an Angular project. Analyze navigation efficiency.",
        "duration": 90,
        "start_date": "2025-11-05T08:30:00",
        "end_date": "2025-11-07T15:00:00",
        "status": "Active",
        "activity_type": "Course Assignment",
    },
    {
        "activity_name": "Laravel Eloquent Relationships",
        "description": "Design and test various Eloquent model relationships (one-to-many, many-to-many, polymorphic) for a blog app.",
        "duration": 180,
        "start_date": "2025-11-08T10:00:00",
        "end_date": "2025-11-09T17:00:00",
        "status": "Active",
        "activity_type": "Workshop",
    },
    {
        "activity_name": "English Debate Preparation",
        "description": "Prepare arguments and counter-arguments for a debate on artificial intelligence in education.",
        "duration": 25,
        "start_date": "2025-11-10T14:00:00",
        "end_date": "2025-11-10T16:30:00",
        "status": "Pending",
        "activity_type": "Assignment",
    },
    {
        "activity_name": "Business Model Canvas Analysis",
        "description": "Break down and assess a startup idea using the Business Model Canvas. Present key components in a team meeting.",
        "duration": 25,
        "start_date": "2025-11-12T09:00:00",
        "end_date": "2025-11-12T12:00:00",
        "status": "Pending",
        "activity_type": "Business Exercise",
    },
    {
        "activity_name": "Public Speaking Practice",
        "description": "Deliver a three-minute speech on sustainable development to improve public speaking skills.",
        "duration": 25,
        "start_date": "2025-11-18T09:00:00",
        "end_date": "2025-11-18T10:00:00",
        "status": "Active",
        "activity_type": "Soft Skills Exercise",
    },
    {
        "activity_name": "Python Pandas Data Cleaning",
        "description": "Clean and preprocess raw survey data using Python Pandas. Document transformations and challenges.",
        "duration": 60,
        "start_date": "2025-11-19T13:30:00",
        "end_date": "2025-11-20T18:00:00",
        "status": "Active",
        "activity_type": "Lab Task",
    }
]

    
    # Get all existing activities once to check for duplicates
    existing_activities = activity_service.get_all_activities()
    existing_activity_names = {act.get("activity_name") for act in existing_activities}
    
    created_count = 0
    skipped_count = 0
    
    for activity_data in activities_data:
        # Check if activity with same name already exists
        if activity_data["activity_name"] in existing_activity_names:
            print(f"  ⚠ Activity '{activity_data['activity_name']}' already exists. Skipping...")
            skipped_count += 1
            continue
        
        # Create the activity
        activity_uri = activity_service.create_activity(
            activity_name=activity_data["activity_name"],
            description=activity_data["description"],
            duration=activity_data["duration"],
            start_date=activity_data["start_date"],
            end_date=activity_data["end_date"],
            status=activity_data["status"],
            activity_type=activity_data["activity_type"],
            instructor_uri=instructor_uri
        )
        
        if activity_uri:
            print(f"  ✓ Created activity: {activity_data['activity_name']} (URI: {activity_uri})")
            created_count += 1
        else:
            print(f"  ✗ Failed to create activity: {activity_data['activity_name']}")
    
    print(f"\n  Summary: {created_count} activities created, {skipped_count} skipped")
    return created_count


def seed_database():
    """Main function to seed the database with initial data."""
    print("=" * 60)
    print("DATABASE SEEDER - Initial Data Population")
    print("=" * 60)
    
    # Check if data already exists
    if check_if_data_exists():
        print("\n⚠ Initial data already exists in the database.")
        print("  To reseed, please clear the existing data first.")
        print("  Exiting without making changes...")
        return False
    
    try:
        # Step 1: Create instructor
        instructor_uri = create_instructor()
        if not instructor_uri:
            print("\n✗ Failed to create instructor. Cannot proceed with activities.")
            return False
        
        # Step 2: Create activities
        activities_created = create_activities(instructor_uri)
        
        # Summary
        print("\n" + "=" * 60)
        print("SEEDING COMPLETE")
        print("=" * 60)
        print(f"✓ Instructor created: {INSTRUCTOR_NAME} ({INSTRUCTOR_EMAIL})")
        print(f"✓ Activities created: {activities_created}")
        print(f"\nYou can now sign in with:")
        print(f"  Email: {INSTRUCTOR_EMAIL}")
        print(f"  Password: {INSTRUCTOR_PASSWORD}")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\nStarting database seeder...")
    print("This script will populate the database with initial data.")
    print("It will only run if no initial data exists.\n")
    
    success = seed_database()
    
    if success:
        print("\n✓ Database seeding completed successfully!")
    else:
        print("\n✗ Database seeding failed or was skipped.")
    
    exit(0 if success else 1)
