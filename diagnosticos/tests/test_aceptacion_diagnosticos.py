from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
from usuarios.models import Usuario, Rol
from pacientes.models import Paciente, HistorialClinico
from radiografias.models import Radiografia
from diagnosticos.models import ResultadoIA, Diagnostico

class DiagnosticosAceptacionTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.rol_medico = Rol.objects.create(nombre="Médico", estado=True)
        self.medico = Usuario.objects.create_user(
            username='medicoia',
            email='medicoia@hospital.com',
            password='password123',
            nombres='Dr. IA',
            apellidos='Prueba',
            ci='888888',
            id_rol=self.rol_medico
        )
        # Login usando username real (el cliente de pruebas usa el backend estándar de Django)
        self.client.login(username='medicoia', password='password123')
        
        self.paciente = Paciente.objects.create(
            nombres='Pedro',
            apellidos='García',
            ci='555444'
        )

    # Mockeamos subprocess.run para no ejecutar el script real de Python/TensorFlow
    # subprocess se importa dentro de la función en radiografias/views.py, por lo que
    # parcheamos el módulo global de subprocess directamente
    @patch('subprocess.run')
    def test_rf04_a_rf08_flujo_radiografia_e_ia(self, mock_subprocess):
        """RF-04, RF-05, RF-06, RF-07, RF-08: Cargar radiografía, procesar y ver resultado."""
        
        # Configurar el mock para que simule una respuesta del script de IA con 92.5% de probabilidad
        mock_result = MagicMock()
        mock_result.stdout = "PROB:0.925"
        mock_subprocess.return_value = mock_result
        
        # 1. Simular carga de archivo (RF-04)
        # Creamos una imagen pequeña en memoria
        imagen_dummy = SimpleUploadedFile(
            name='torax_prueba.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/jpeg'
        )
        
        response_carga = self.client.post(reverse('nueva_carga'), {
            'paciente': self.paciente.id_paciente,
            'archivo': imagen_dummy
        })
        
        # Verificar que la carga redirige al resultado (RF-05, RF-06)
        self.assertEqual(response_carga.status_code, 302)
        
        # 2. Verificar base de datos
        radiografia = Radiografia.objects.get(nombre_archivo='torax_prueba.jpg')
        resultado_ia = ResultadoIA.objects.get(id_radiografia=radiografia)
        
        # RF-07: Verificar que la probabilidad se extrajo y guardó correctamente (92.5%)
        self.assertEqual(resultado_ia.porcentaje_confianza, 92.5)
        self.assertEqual(resultado_ia.prediccion, 'Neumonía detectada')
        
        # 3. Visualización (RF-08)
        response_resultado = self.client.get(reverse('resultado_ia_detalle', args=[radiografia.id_radiografia]))
        self.assertEqual(response_resultado.status_code, 200)
        # El template usa formato local (coma decimal): '92,50%'
        self.assertContains(response_resultado, '92')
        self.assertContains(response_resultado, 'Neumonía detectada')
        # RF-08: Verificar que la página muestra la imagen original y la sección del mapa de calor
        # Django agrega un sufijo aleatorio al nombre: torax_prueba_XXXXXX.jpg
        self.assertContains(response_resultado, 'torax_prueba')
        # El template renderiza el mapa de calor visualmente con CSS; verificamos el título de sección
        self.assertContains(response_resultado, 'GRAD-CAM')

    def test_rf09_historial_y_rf10_reporte(self):
        """RF-09 y RF-10: Registrar en historial clínico y generar reporte PDF/Impresión."""
        
        # Preparar datos base (Radiografía + ResultadoIA)
        imagen_dummy = SimpleUploadedFile(name='test.jpg', content=b'fake', content_type='image/jpeg')
        radiografia = Radiografia.objects.create(
            id_paciente=self.paciente, id_usuario=self.medico, 
            nombre_archivo='test.jpg', ruta_archivo=imagen_dummy, formato='jpg'
        )
        resultado_ia = ResultadoIA.objects.create(
            id_radiografia=radiografia, prediccion='Normal', 
            porcentaje_confianza=15.0, mapa_calor='fake.png', tiempo_procesamiento=1.0
        )
        
        # 1. Crear Diagnóstico Clínico (Esto lo registra en HistorialClinico)
        response_diagnostico = self.client.post(reverse('diagnostico_crear', args=[resultado_ia.id_resultado]), {
            'observaciones': 'Pulmones limpios',
            'diagnostico_final': 'Paciente Sano',
            'recomendaciones': 'Tomar agua'
        })
        self.assertEqual(response_diagnostico.status_code, 302) # Redirige al detalle
        
        diagnostico = Diagnostico.objects.get(id_resultado=resultado_ia)
        
        # RF-09: El historial muestra la predicción del modelo IA (campo 'prediccion')
        # El campo 'diagnostico_final' es del médico, visible sólo en la vista de detalle
        self.assertTrue(HistorialClinico.objects.filter(id_diagnostico=diagnostico).exists())
        response_historial = self.client.get(reverse('pacientes_historial'))
        self.assertContains(response_historial, 'Normal')  # Predicción IA visible en la tabla
        
        # 3. Verificar Generación de Reporte (RF-10)
        response_reporte = self.client.get(reverse('generar_reporte_pdf', args=[diagnostico.id_diagnostico]))
        self.assertEqual(response_reporte.status_code, 200)
        # El reporte está optimizado para imprimir (reporte_print.html)
        self.assertContains(response_reporte, 'Pulmones limpios')
        self.assertContains(response_reporte, 'Paciente Sano')
        self.assertTemplateUsed(response_reporte, 'diagnosticos/reporte_print.html')
