from django.db import models
from radiografias.models import Radiografia
from usuarios.models import Usuario

class ResultadoIA(models.Model):
    id_resultado = models.AutoField(primary_key=True)
    id_radiografia = models.ForeignKey(Radiografia, on_delete=models.CASCADE, db_column='id_radiografia')
    prediccion = models.TextField(blank=True, null=True)
    porcentaje_confianza = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    mapa_calor = models.CharField(max_length=255, blank=True, null=True)
    tiempo_procesamiento = models.FloatField(blank=True, null=True)
    modelo_ia = models.CharField(max_length=100, blank=True, null=True)
    fecha_analisis = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'resultados_ia'


class Diagnostico(models.Model):
    id_diagnostico = models.AutoField(primary_key=True)
    id_resultado = models.ForeignKey(ResultadoIA, on_delete=models.CASCADE, db_column='id_resultado')
    id_usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, db_column='id_usuario')
    observaciones = models.TextField(blank=True, null=True)
    diagnostico_final = models.TextField(blank=True, null=True)
    recomendaciones = models.TextField(blank=True, null=True)
    fecha_diagnostico = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'diagnosticos'


class Reporte(models.Model):
    id_reporte = models.AutoField(primary_key=True)
    id_diagnostico = models.ForeignKey(Diagnostico, on_delete=models.CASCADE, db_column='id_diagnostico')
    tipo_reporte = models.CharField(max_length=100, blank=True, null=True)
    ruta_pdf = models.FileField(upload_to='reportes/', blank=True, null=True)
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reportes'
