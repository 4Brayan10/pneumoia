from django.db import models
from pacientes.models import Paciente
from usuarios.models import Usuario

class Radiografia(models.Model):
    id_radiografia = models.AutoField(primary_key=True)
    id_paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, db_column='id_paciente')
    id_usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, db_column='id_usuario')
    nombre_archivo = models.CharField(max_length=255)
    ruta_archivo = models.FileField(upload_to='radiografias/')
    formato = models.CharField(max_length=50, blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    estado_procesamiento = models.CharField(max_length=50, default='Pendiente')

    def __str__(self):
        return f"Radiografía {self.id_radiografia} - {self.id_paciente}"

    class Meta:
        db_table = 'radiografias'
