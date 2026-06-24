# pyrefly: ignore [missing-import]
from django.urls import path
from . import views

urlpatterns = [
    path('panel/', views.panel_principal, name='panel_principal'),
]
