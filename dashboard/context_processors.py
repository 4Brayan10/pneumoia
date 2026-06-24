from diagnosticos.models import ResultadoIA

def notificaciones(request):
    if request.user.is_authenticated:
        # Obtener los ultimos 5 resultados de IA generados
        ultimos_resultados = ResultadoIA.objects.select_related('id_radiografia__id_paciente').order_by('-fecha_analisis')[:5]
        return {
            'notificaciones_ia': ultimos_resultados,
            'notificaciones_count': ultimos_resultados.count()
        }
    return {}
