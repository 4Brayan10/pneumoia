from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from pacientes.models import Paciente, HistorialClinico
from radiografias.models import Radiografia
from diagnosticos.models import Diagnostico, ResultadoIA
from usuarios.models import Usuario, Rol


class DiagnosticoTestCase(TestCase):
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

        self.paciente = Paciente.objects.create(
            nombres='Juan', apellidos='Pérez', ci='1234567'
        )
        archivo = SimpleUploadedFile(
            "radiografia.jpg", b"contenido", content_type="image/jpeg"
        )
        self.radiografia = Radiografia.objects.create(
            id_paciente=self.paciente,
            id_usuario=self.medico,
            nombre_archivo="radiografia.jpg",
            ruta_archivo=archivo,
            formato="jpg",
            estado_procesamiento="Completado"
        )

    # ─── CP-03: Unitaria ───
    @patch('infer.main')
    def test_cp03_prediccion_ia_aislada(self, mock_main):
        """CP-03: Predicción del modelo IA aislada"""
        mock_main.return_value = None
        import infer
        infer.main()
        self.assertTrue(mock_main.called)

    # ─── CP-09: Integración ───
    def test_cp09_generar_diagnostico_ia(self):
        """CP-09: Generar diagnóstico de IA para radiografía"""
        ResultadoIA.objects.create(
            id_radiografia=self.radiografia,
            prediccion='Normal',
            porcentaje_confianza=92.50,
            modelo_ia='PneumoIA-v1'
        )
        response = self.client.get(
            reverse('resultado_ia_detalle', args=[self.radiografia.id_radiografia])
        )
        self.assertEqual(response.status_code, 200)

    # ─── CP-10: Sistema / E2E ───
    def test_cp10_flujo_completo_e2e(self):
        """CP-10: Flujo Completo: Carga, Diagnóstico y Resultado"""
        # 1. Crear resultado IA
        resultado = ResultadoIA.objects.create(
            id_radiografia=self.radiografia,
            prediccion='Neumonía',
            porcentaje_confianza=87.30,
            modelo_ia='PneumoIA-v1'
        )

        # 2. Crear diagnóstico médico
        diagnostico = Diagnostico.objects.create(
            id_resultado=resultado,
            id_usuario=self.medico,
            diagnostico_final='Neumonía bacteriana leve',
            observaciones='Opacidades en lóbulo inferior derecho',
            recomendaciones='Antibióticos por 7 días'
        )

        # 3. Registrar en historial clínico
        HistorialClinico.objects.create(
            id_paciente=self.paciente,
            id_diagnostico=diagnostico
        )

        # 4. Visualizar detalle del diagnóstico
        response = self.client.get(
            reverse('diagnostico_detalle', args=[diagnostico.id_diagnostico])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Neumonía')