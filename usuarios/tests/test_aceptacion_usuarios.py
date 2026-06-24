from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from usuarios.models import Usuario, Rol

# Helper: saltear la validación del reCAPTCHA en tests
CAPTCHA_BYPASS = patch(
    'django_recaptcha.fields.ReCaptchaField.validate',
    return_value=True
)

class UsuariosAceptacionTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Crear roles base
        self.rol_admin = Rol.objects.create(nombre="Administrador", estado=True)
        self.rol_medico = Rol.objects.create(nombre="Médico", estado=True)
        
        # Crear un administrador para probar las funcionalidades de RF-11
        self.admin = Usuario.objects.create_user(
            username='admin123',
            email='admin@hospital.com',
            password='adminpassword',
            nombres='Admin',
            apellidos='Sistema',
            ci='111111',
            id_rol=self.rol_admin
        )

    # --- RF-01: Registro de usuarios ---
    def test_rf01_registro_medico_exitoso(self):
        """RF-01: El sistema debe permitir registrar usuarios validando que no existan duplicados."""
        datos_registro = {
            'nombres': 'Carlos',
            'apellidos': 'Ramírez',
            'ci': '555555',
            'telefono': '77788899',
            'email': 'carlos@hospital.com',
            'password': 'securepass123',
            'confirm_password': 'securepass123',
            'id_rol': self.rol_medico.id_rol
        }
        response = self.client.post(reverse('registro'), datos_registro)
        
        # Si el registro es exitoso, inicia sesión y redirige al panel principal
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('panel_principal'))
        
        # Validar en base de datos
        self.assertTrue(Usuario.objects.filter(email='carlos@hospital.com').exists())

    def test_rf01_registro_usuario_duplicado(self):
        """RF-01: Validar que no existan usuarios duplicados (mismo correo o generado)."""
        # Crear el primero
        self.test_rf01_registro_medico_exitoso()
        
        # Intentar registrar otro con el mismo email
        datos_registro = {
            'nombres': 'Otro',
            'apellidos': 'Médico',
            'ci': '666666',
            'telefono': '77788800',
            'email': 'carlos@hospital.com', # Email duplicado
            'password': 'securepass123',
            'confirm_password': 'securepass123',
            'id_rol': self.rol_medico.id_rol
        }
        response = self.client.post(reverse('registro'), datos_registro)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ya existe un usuario con ese correo electrónico')

    # --- RF-02: Inicio de sesión ---
    @CAPTCHA_BYPASS
    def test_rf02_inicio_sesion_valido_y_restringido(self, mock_captcha=None):
        """RF-02: Inicio de sesión validando credenciales y restringiendo accesos."""
        # 1. Credenciales válidas
        response_valido = self.client.post(reverse('login'), {
            'username': 'admin@hospital.com',
            'password': 'adminpassword',
            'g-recaptcha-response': 'bypass_test'
        })
        self.assertEqual(response_valido.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)
        
        self.client.logout()

        # 2. Credenciales inválidas (restringiendo el acceso)
        response_invalido = self.client.post(reverse('login'), {
            'username': 'admin@hospital.com',
            'password': 'claveincorrecta',
            'g-recaptcha-response': 'bypass_test'
        })
        self.assertEqual(response_invalido.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertContains(response_invalido, 'contraseña es incorrecta')

    # --- RF-11: Gestión de usuarios (CRUD como Administrador) ---
    @CAPTCHA_BYPASS
    def test_rf11_gestion_de_usuarios_por_admin(self, mock_captcha=None):
        """RF-11: El administrador debe poder crear, editar, eliminar usuarios y asignar roles."""
        # Hacer login como administrador
        self.client.login(username='admin123', password='adminpassword')
        
        # 1. Crear nuevo usuario desde panel de admin
        response_crear = self.client.post(reverse('crear_usuario'), {
            'nombres': 'Ana',
            'apellidos': 'Torres',
            'ci': '999888',
            'telefono': '66655544',
            'email': 'ana@hospital.com',
            'password': 'anapassword',
            'confirm_password': 'anapassword',
            'id_rol': self.rol_medico.id_rol,
            'estado': 'on'
        })
        self.assertEqual(response_crear.status_code, 302)
        usuario_creado = Usuario.objects.get(email='ana@hospital.com')
        self.assertEqual(usuario_creado.id_rol, self.rol_medico)

        # 2. Editar usuario
        response_editar = self.client.post(reverse('editar_usuario', args=[usuario_creado.id_usuario]), {
            'nombres': 'Ana María',
            'apellidos': 'Torres',
            'ci': '999888',
            'telefono': '66655544',
            'email': 'ana@hospital.com',
            'id_rol': self.rol_admin.id_rol, # Cambiando el rol a admin
            'estado': 'on'
        })
        self.assertEqual(response_editar.status_code, 302)
        usuario_creado.refresh_from_db()
        self.assertEqual(usuario_creado.nombres, 'Ana María')
        self.assertEqual(usuario_creado.id_rol, self.rol_admin) # Rol asignado actualizado

        # 3. Eliminar usuario
        response_eliminar = self.client.post(reverse('eliminar_usuario', args=[usuario_creado.id_usuario]))
        self.assertEqual(response_eliminar.status_code, 302)
        self.assertFalse(Usuario.objects.filter(email='ana@hospital.com').exists())
