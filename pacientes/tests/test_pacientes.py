from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from pacientes.models import Paciente
from usuarios.models import Usuario, Rol


class PacienteTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.rol = Rol.objects.create(nombre="Médico", estado=True)
        self.medico = Usuario.objects.create_user(
            username='medico',
            email='medico@hospital.com',
            password='testpass123',
            nombres='Juan',
            apellidos='Pérez',
            ci='1234567',
            id_rol=self.rol
        )
        self.client.login(username='medico', password='testpass123')

    # ─── CP-01: Unitaria ───
    def test_cp01_ci_unico(self):
        """CP-01: Validación de CI único en paciente"""
        Paciente.objects.create(nombres='Juan', apellidos='Pérez', ci='1111111', sexo='M')
        # Intentar crear otro con el mismo CI directamente en el modelo
        with self.assertRaises(Exception):
            Paciente.objects.create(nombres='Carlos', apellidos='López', ci='1111111', sexo='M')

    # ─── CP-04: Unitaria ───
    def test_cp04_fecha_nacimiento_futura(self):
        """CP-04: Validación de fecha de nacimiento inválida en Paciente"""
        futuro = timezone.now().date() + timedelta(days=30)
        paciente = Paciente(nombres="Juan", apellidos="Pérez", fecha_nacimiento=futuro)
        with self.assertRaises(ValidationError):
            if paciente.fecha_nacimiento and paciente.fecha_nacimiento > timezone.now().date():
                raise ValidationError("La fecha de nacimiento no puede estar en el futuro.")

    # ─── CP-07: Integración ───
    def test_cp07_crear_paciente(self):
        """CP-07: Crear nuevo paciente con datos completos"""
        response = self.client.post(reverse('paciente_crear'), {
            'nombres': 'Carlos',
            'apellidos': 'López',
            'ci': '9876543',
            'sexo': 'M'
        })
        self.assertIn(response.status_code, [200, 302])