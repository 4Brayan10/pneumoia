# pyrefly: ignore [missing-import]
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('login/registro/', views.registro, name='registro'),
    path('logout/', views.cerrar_sesion, name='logout'),
    
    # User Management (CRUD)
    path('lista/', views.lista_usuarios, name='lista_usuarios'),
    path('historial-accesos/', views.historial_accesos, name='historial_accesos'),
    path('crear/', views.crear_usuario, name='crear_usuario'),
    path('editar/<int:id>/', views.editar_usuario, name='editar_usuario'),
    path('eliminar/<int:id>/', views.eliminar_usuario, name='eliminar_usuario'),

    # Roles Management (CRUD)
    path('roles/', views.lista_roles, name='lista_roles'),
    path('roles/crear/', views.crear_rol, name='crear_rol'),
    path('roles/editar/<int:id_rol>/', views.editar_rol, name='editar_rol'),
    path('roles/eliminar/<int:id_rol>/', views.eliminar_rol, name='eliminar_rol'),
]
