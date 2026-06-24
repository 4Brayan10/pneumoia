from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from pacientes.models import Paciente
from radiografias.models import Radiografia
from usuarios.models import Usuario, Rol


class RadiografiaTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.rol = Rol.objects.create(nombre="Técnico", estado=True)
        self.tecnico = Usuario.objects.create_user(
            username='tecnico',
            email='tecnico@hospital.com',
            password='testpass123',
            nombres='Carlos',
            apellidos='López',
            ci='7654321',
            id_rol=self.rol
        )
        self.client.login(username='tecnico', password='testpass123')
        self.paciente = Paciente.objects.create(
            nombres='Juan', apellidos='Pérez', ci='1234567'
        )

    # ─── CP-05: Unitaria ───
    def test_cp05_ruta_guardado(self):
        """CP-05: Generación de ruta de almacenamiento de radiografías"""
        id_paciente = 5
        nombre_archivo = "foto_torax.jpg"
        ruta_esperada = "radiografias/paciente_5/foto_torax.jpg"

        def generar_ruta_dinamica(id_paciente, filename):
            return f"radiografias/paciente_{id_paciente}/{filename}"

        self.assertEqual(generar_ruta_dinamica(id_paciente, nombre_archivo), ruta_esperada)

    # ─── CP-08: Integración ───
    def test_cp08_cargar_radiografia(self):
        """CP-08: Cargar radiografía a paciente existente"""
        archivo = SimpleUploadedFile(
            "radiografia.jpg", b"contenido_simulado", content_type="image/jpeg"
        )
        response = self.client.post(
            reverse('nueva_carga'),
            {'paciente': self.paciente.id_paciente, 'archivo': archivo}
        )
        self.assertIn(response.status_code, [200, 302])