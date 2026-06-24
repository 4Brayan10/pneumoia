from django.urls import path
from . import views

urlpatterns = [
    path('', views.diagnostico_view, name='diagnostico_lista'),
    path('lista/', views.diagnostico_view, name='diagnostico'), # backward compatibility
    path('resultado-ia/<int:id_radiografia>/', views.resultado_ia_detalle, name='resultado_ia_detalle'),
    path('crear/<int:id_resultado>/', views.diagnostico_crear, name='diagnostico_crear'),
    path('detalle/<int:id_diagnostico>/', views.diagnostico_detalle, name='diagnostico_detalle'),
    path('reporte/<int:id_diagnostico>/pdf/', views.generar_reporte_pdf, name='generar_reporte_pdf'),
]
