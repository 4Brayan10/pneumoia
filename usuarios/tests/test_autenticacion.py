from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from usuarios.models import Usuario, Rol


# Helper: saltear la validación del reCAPTCHA en tests
CAPTCHA_BYPASS = patch(
    'django_recaptcha.fields.ReCaptchaField.validate',
    return_value=True
)


class LoginTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.rol = Rol.objects.create(nombre="Médico", estado=True)
        self.user = Usuario.objects.create_user(
            username='medico',
            email='medico@hospital.com',
            password='testpass123',
            nombres='Juan',
            apellidos='Pérez',
            ci='1234567',
            id_rol=self.rol
        )

    # ─── CP-02: Unitaria ───
    @CAPTCHA_BYPASS
    def test_cp02_login_vacio(self, mock_captcha=None):
        """CP-02: Validación de formulario de login vacío"""
        response = self.client.post(reverse('login'), {
            'username': '',
            'password': '',
            'g-recaptcha-response': 'bypass_test'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'obligatorios')
        self.assertNotIn('_auth_user_id', self.client.session)

    # ─── CP-06: Integración ───
    @CAPTCHA_BYPASS
    def test_cp06_login_exitoso(self, mock_captcha=None):
        """CP-06: Login exitoso con credenciales válidas"""
        response = self.client.post(reverse('login'), {
            'username': 'medico@hospital.com',
            'password': 'testpass123',
            'g-recaptcha-response': 'bypass_test'
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)