from django.test import TestCase, Client
from django.urls import reverse
from usuarios.models import Usuario, Rol
from pacientes.models import Paciente

class PacientesAceptacionTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.rol_medico = Rol.objects.create(nombre="Médico", estado=True)
        self.medico = Usuario.objects.create_user(
            username='medicoprueba',
            email='medico@hospital.com',
            password='password123',
            nombres='José',
            apellidos='Gómez',
            ci='123123',
            id_rol=self.rol_medico
        )
        # Login usando username real (el cliente de pruebas de Django usa el backend estándar)
        self.client.login(username='medicoprueba', password='password123')

    # --- RF-03: Gestión de pacientes (CRUD) ---
    def test_rf03_flujo_completo_pacientes(self):
        """RF-03: Registrar, consultar, editar y eliminar información de pacientes."""
        
        # 1. Registrar Paciente
        datos_paciente = {
            'nombres': 'María',
            'apellidos': 'Lopez',
            'ci': '9876543',
            'fecha_nacimiento': '2015-05-10',
            'sexo': 'F',
            'peso': '25.5',
            'talla': '1.20',
            'nombre_tutor': 'Juan Lopez',
            'telefono_tutor': '77712345'
        }
        
        response_crear = self.client.post(reverse('paciente_crear'), datos_paciente)
        self.assertEqual(response_crear.status_code, 302) # Redirige a lista
        
        paciente_creado = Paciente.objects.get(ci='9876543')
        self.assertEqual(paciente_creado.nombres, 'María')
        
        # 2. Consultar Paciente
        response_lista = self.client.get(reverse('pacientes_lista'))
        self.assertEqual(response_lista.status_code, 200)
        self.assertContains(response_lista, 'María')
        self.assertContains(response_lista, 'Lopez')
        
        # Consultar detalle
        response_detalle = self.client.get(reverse('paciente_detalle', args=[paciente_creado.id_paciente]))
        self.assertEqual(response_detalle.status_code, 200)
        self.assertContains(response_detalle, 'María Lopez')
        # El template muestra el peso con formato local: '25,50 kg'
        self.assertContains(response_detalle, '25')
        
        # 3. Editar Paciente
        datos_editados = datos_paciente.copy()
        datos_editados['peso'] = '26.0' # Cambio de peso
        
        response_editar = self.client.post(reverse('paciente_editar', args=[paciente_creado.id_paciente]), datos_editados)
        self.assertEqual(response_editar.status_code, 302)
        
        paciente_creado.refresh_from_db()
        self.assertEqual(str(paciente_creado.peso), '26.00')
        
        # 4. Eliminar Paciente
        response_eliminar = self.client.post(reverse('paciente_eliminar', args=[paciente_creado.id_paciente]))
        self.assertEqual(response_eliminar.status_code, 302)
        
        self.assertFalse(Paciente.objects.filter(ci='9876543').exists())
