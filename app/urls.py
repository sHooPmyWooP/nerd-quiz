from django.urls import path

from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('quiz/create/', views.quiz_create, name='quiz_create'),
    path('quiz/<int:pk>/edit/', views.quiz_edit, name='quiz_edit'),
    path('quiz/<int:pk>/delete/', views.quiz_delete, name='quiz_delete'),
    path('quiz/<int:pk>/sessions/', views.quiz_sessions, name='quiz_sessions'),
    path('quiz/<int:pk>/categories/', views.quiz_add_categories, name='quiz_add_categories'),
    path('quiz/<int:pk>/questions/', views.quiz_add_questions, name='quiz_add_questions'),
    path('quiz/<int:quiz_pk>/play/', views.play_start, name='play_start'),
    path('session/<int:session_pk>/teams/', views.play_add_teams, name='play_add_teams'),
    path('session/<int:session_pk>/play/', views.play, name='play'),
    path('session/<int:session_pk>/award/', views.play_award, name='play_award'),
    path('session/<int:session_pk>/grant-points/', views.play_grant_points, name='play_grant_points'),
    path('session/<int:session_pk>/deduct/', views.play_deduct, name='play_deduct'),
    path('session/<int:session_pk>/double/', views.play_double_points, name='play_double_points'),
    path('session/<int:session_pk>/selector/', views.play_set_selector, name='play_set_selector'),
    path('session/<int:session_pk>/reset/', views.play_reset, name='play_reset'),
]
