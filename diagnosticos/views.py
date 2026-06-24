from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from usuarios.decorators import es_personal_medico, es_medico_o_admin
from django.contrib import messages
from .models import ResultadoIA, Diagnostico, Reporte
from radiografias.models import Radiografia
from pacientes.models import Paciente, HistorialClinico
from django.http import HttpResponse

@user_passes_test(es_personal_medico, login_url='login')
def diagnostico_view(request):
    # Vista general para redirigir o listar diagnósticos
    diagnosticos = Diagnostico.objects.all().order_by('-fecha_diagnostico')
    return render(request, 'diagnostico.html', {'diagnosticos': diagnosticos})

@user_passes_test(es_personal_medico, login_url='login')
def resultado_ia_detalle(request, id_radiografia):
    radiografia = get_object_or_404(Radiografia, id_radiografia=id_radiografia)
    resultado = get_object_or_404(ResultadoIA, id_radiografia=radiografia)
    return render(request, 'resultado_ia_detalle.html', {
        'radiografia': radiografia,
        'resultado': resultado
    })

@user_passes_test(es_medico_o_admin, login_url='login')
def diagnostico_crear(request, id_resultado):
    resultado = get_object_or_404(ResultadoIA, id_resultado=id_resultado)
    radiografia = resultado.id_radiografia
    paciente = radiografia.id_paciente
    
    if request.method == 'POST':
        observaciones = request.POST.get('observaciones')
        diagnostico_final = request.POST.get('diagnostico_final')
        recomendaciones = request.POST.get('recomendaciones')
        
        diagnostico = Diagnostico.objects.create(
            id_resultado=resultado,
            id_usuario=request.user,
            observaciones=observaciones,
            diagnostico_final=diagnostico_final,
            recomendaciones=recomendaciones
        )
        
        # Registrar en HistorialClinico
        HistorialClinico.objects.create(
            id_paciente=paciente,
            id_diagnostico=diagnostico
        )
        
        messages.success(request, 'Diagnóstico clínico registrado y guardado en el historial.')
        return redirect('diagnostico_detalle', id_diagnostico=diagnostico.id_diagnostico)
        
    return render(request, 'diagnostico.html', {
        'resultado': resultado,
        'radiografia': radiografia,
        'paciente': paciente
    })

@user_passes_test(es_personal_medico, login_url='login')
def diagnostico_detalle(request, id_diagnostico):
    diagnostico = get_object_or_404(Diagnostico, id_diagnostico=id_diagnostico)
    resultado = diagnostico.id_resultado
    radiografia = resultado.id_radiografia
    paciente = radiografia.id_paciente
    return render(request, 'diagnostico_detalle.html', {
        'diagnostico': diagnostico,
        'resultado': resultado,
        'radiografia': radiografia,
        'paciente': paciente
    })

@user_passes_test(es_personal_medico, login_url='login')
def generar_reporte_pdf(request, id_diagnostico):
    # En lugar de requerir reportlab o weasyprint que podrían fallar por dependencias de sistema,
    # generamos una plantilla HTML ultra-limpia optimizada para imprimir ("Guardar como PDF")
    diagnostico = get_object_or_404(Diagnostico, id_diagnostico=id_diagnostico)
    resultado = diagnostico.id_resultado
    radiografia = resultado.id_radiografia
    paciente = radiografia.id_paciente
    
    context = {
        'diagnostico': diagnostico,
        'resultado': resultado,
        'radiografia': radiografia,
        'paciente': paciente
    }
    # Retornamos una respuesta HTML de impresión directa
    return render(request, 'diagnosticos/reporte_print.html', context)