from django.db import models
from usuarios.models import Usuario

class Paciente(models.Model):
    id_paciente = models.AutoField(primary_key=True)
    # Reemplazamos la tabla Persona por campos directos, igual que en Usuario
    ci = models.CharField(max_length=20, unique=True, null=True, blank=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    sexo = models.CharField(max_length=1, blank=True, null=True)
    peso = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    talla = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    telefono_tutor = models.CharField(max_length=20, blank=True, null=True)
    nombre_tutor = models.CharField(max_length=150, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

    class Meta:
        db_table = 'pacientes'


class HistorialClinico(models.Model):
    id_historial = models.AutoField(primary_key=True)
    id_paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, db_column='id_paciente')
    # id_diagnostico se agregará luego o como cadena de texto si hay dependencias circulares
    # Lo referenciamos usando el string 'diagnosticos.Diagnostico' para evitar importaciones circulares
    id_diagnostico = models.ForeignKey('diagnosticos.Diagnostico', on_delete=models.CASCADE, db_column='id_diagnostico', null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historial_clinico'
