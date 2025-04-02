from django.urls import path
from . import views

urlpatterns = [
    path('nurse_dashboard/', views.nurse_dashboard, name='nurse_dashboard'),
    path('nurse_profile/', views.nurse_profile, name='nurse_profile'),
]