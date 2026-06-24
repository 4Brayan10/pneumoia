from django.urls import path
from . import views

urlpatterns = [
    path('', views.pacientes_view, name='pacientes_lista'),
    path('historial/', views.historial_view, name='pacientes_historial'),
    path('detalle/<int:id_paciente>/', views.paciente_detalle, name='paciente_detalle'),
    path('crear/', views.paciente_crear, name='paciente_crear'),
    path('editar/<int:id_paciente>/', views.paciente_editar, name='paciente_editar'),
    path('eliminar/<int:id_paciente>/', views.paciente_eliminar, name='paciente_eliminar'),
    path('historial/eliminar/<int:id_historial>/', views.historial_eliminar, name='historial_eliminar'),
]