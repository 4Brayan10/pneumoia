# pyrefly: ignore [missing-import]
from django.shortcuts import render
# pyrefly: ignore [missing-import]
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from pacientes.models import Paciente
from diagnosticos.models import Diagnostico, ResultadoIA

# Create your views here.


@login_required(login_url='login')
def panel_principal(request):
    import datetime
    hoy = timezone.localdate()
    total_pacientes = Paciente.objects.count()
    analisis_hoy = ResultadoIA.objects.filter(fecha_analisis__date=hoy).count()
    reportes_pendientes = Diagnostico.objects.filter(reporte__isnull=True).count()

    # Cálculo de actividad semanal (últimos 7 días)
    dias_semana_nombres = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM']
    actividad_semanal = []
    fecha_inicio = hoy - datetime.timedelta(days=6)
    
    analisis_semana = ResultadoIA.objects.filter(fecha_analisis__date__gte=fecha_inicio, fecha_analisis__date__lte=hoy)
    
    conteo_por_dia = {fecha_inicio + datetime.timedelta(days=i): 0 for i in range(7)}
    for analisis in analisis_semana:
        fecha_analisis = timezone.localtime(analisis.fecha_analisis).date()
        if fecha_analisis in conteo_por_dia:
            conteo_por_dia[fecha_analisis] += 1
            
    max_actividad = max(conteo_por_dia.values()) if conteo_por_dia.values() else 0
    
    for i in range(7):
        dia_actual = fecha_inicio + datetime.timedelta(days=i)
        cantidad = conteo_por_dia[dia_actual]
        # Min height for visibility
        if cantidad == 0:
            porcentaje = 15
        else:
            porcentaje = (cantidad / max_actividad * 85) + 15  # Scale between 15% and 100%
            
        actividad_semanal.append({
            'label': dias_semana_nombres[dia_actual.weekday()],
            'porcentaje': porcentaje,
            'cantidad': cantidad,
            'activo': dia_actual == hoy
        })

    return render(request, 'panelPrincipal.html', {
        'total_pacientes': f'{total_pacientes:,}',
        'analisis_hoy': f'{analisis_hoy:,}',
        'reportes_pendientes': f'{reportes_pendientes:,}',
        'actividad_semanal': actividad_semanal,
    })
