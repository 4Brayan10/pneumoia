from django.urls import path
from . import views

urlpatterns = [
    path('', views.nueva_carga_view, name='nueva_carga'),
    path('paciente/<int:id_paciente>/', views.lista_radiografias, name='lista_radiografias'),
    path('eliminar/<int:id_radiografia>/', views.radiografia_eliminar, name='radiografia_eliminar'),
]
