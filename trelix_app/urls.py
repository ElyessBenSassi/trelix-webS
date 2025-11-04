"""
URL configuration for trelix_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views
from goal import views as goal_views
from leaderboared import views as leaderboard_views

urlpatterns = [
    path('', views.home, name='home'),  
    path('classes/', views.classes_html_view),
    
    # Main goal list
    path('goals/', goal_views.goal_list, name='goal_list'),
    
    # Create goal
    path('goals/create/', goal_views.goal_create, name='goal_create'),
    
    # Specific actions with UUID
    path('goals/<str:goal_id>/delete/', goal_views.goal_delete, name='goal_delete'),
    path('goals/<str:goal_id>/toggle/', goal_views.goal_toggle, name='goal_toggle'),
    
    # Edit by title (must come AFTER UUID routes)
    path('goals/edit/<str:goal_title>/', goal_views.goal_edit, name='goal_edit'),
 # Quiz
    path('quiz/', leaderboard_views.quiz_list, name='quiz_list'),
    path('quiz/create/', leaderboard_views.quiz_create, name='create_quiz'),

    path('quiz/<str:quiz_id>/', leaderboard_views.quiz_detail, name='quiz_detail'),
   # trelix_app/urls.py

path('quiz/<str:quiz_id>/join', leaderboard_views.join_quiz, name='join_quiz'),  # ← NO trailing /  # ← NO /
    path('quiz/<str:quiz_id>/take/', leaderboard_views.quiz_take, name='quiz_take'),
    path('quiz/<str:quiz_id>/submit/', leaderboard_views.quiz_submit, name='quiz_submit'),

    path('quiz/<str:quiz_id>/update/', leaderboard_views.update_quiz, name='update_quiz'),
    path('quiz/<str:quiz_id>/delete/', leaderboard_views.delete_quiz, name='delete_quiz'),

    path('quiz/<str:quiz_id>/leaderboard/', leaderboard_views.quiz_leaderboard, name='quiz_leaderboard'),
    path('leaderboard/', leaderboard_views.leaderboard_list, name='leaderboard_list'),
    path('generate-goal-description/', goal_views.generate_goal_description, name='generate_goal_description'),
]