from django.urls import path

from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('quiz/create/', views.quiz_create, name='quiz_create'),
    path('quiz/<int:pk>/edit/', views.quiz_edit, name='quiz_edit'),
    path('quiz/<int:quiz_pk>/play/', views.play_start, name='play_start'),
    path('session/<int:session_pk>/teams/', views.play_add_teams, name='play_add_teams'),
    path('quiz/<int:pk>/categories/', views.quiz_add_categories, name='quiz_add_categories'),
    path('quiz/<int:pk>/questions/', views.quiz_add_questions, name='quiz_add_questions'),
]
