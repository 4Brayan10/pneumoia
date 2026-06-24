from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from usuarios.decorators import es_personal_medico, es_medico_o_admin
from django.db.models import Q
from .models import Paciente, HistorialClinico
from .forms import PacienteForm

#Para mas seguridad se agrega @login_required
@user_passes_test(es_personal_medico, login_url='login')
def pacientes_view(request):
    query = request.GET.get('q', '')
    if query:
        pacientes = Paciente.objects.filter(
            Q(nombres__icontains=query) | 
            Q(apellidos__icontains=query) |
            Q(ci__icontains=query)
        ).order_by('-fecha_registro')
    else:
        pacientes = Paciente.objects.all().order_by('-fecha_registro')
    return render(request, 'paciente.html', {'pacientes': pacientes, 'query': query})

@user_passes_test(es_personal_medico, login_url='login')
def historial_view(request):
    query = request.GET.get('q', '')
    diagnostico = request.GET.get('diagnostico', '')
    fecha = request.GET.get('fecha', '')
    
    historial = HistorialClinico.objects.select_related(
        'id_paciente',
        'id_diagnostico__id_resultado__id_radiografia',
        'id_diagnostico__id_usuario'
    ).all()

    if query:
        from django.db.models import Q
        q_obj = Q(id_paciente__nombres__icontains=query) | Q(id_paciente__apellidos__icontains=query)
        
        # Si el texto es un número, buscamos también por ID exacto
        if query.isdigit():
            q_obj |= Q(id_paciente__id_paciente=int(query))
            
        # Opcional: permitir buscar "Neumonía" o "Normal" desde la misma caja de texto
        q_obj |= Q(id_diagnostico__id_resultado__prediccion__icontains=query)
        
        historial = historial.filter(q_obj)
        
    if diagnostico:
        historial = historial.filter(id_diagnostico__id_resultado__prediccion=diagnostico)
        
    if fecha:
        from datetime import timedelta
        from django.utils import timezone
        dias = int(fecha)
        fecha_limite = timezone.now() - timedelta(days=dias)
        historial = historial.filter(fecha_registro__gte=fecha_limite)

    historial = historial.order_by('-fecha_registro')
    return render(request, 'historialClinico.html', {'historial': historial})

@user_passes_test(es_personal_medico, login_url='login')
def paciente_detalle(request, id_paciente):
    paciente = get_object_or_404(Paciente, id_paciente=id_paciente)
    historial = HistorialClinico.objects.filter(
        id_paciente=paciente
    ).select_related(
        'id_diagnostico__id_resultado__id_radiografia',
        'id_diagnostico__id_usuario'
    ).order_by('-fecha_registro')
    return render(request, 'paciente_detalle.html', {
        'paciente': paciente,
        'historial': historial,
    })

@user_passes_test(es_personal_medico, login_url='login')
def paciente_crear(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('pacientes_lista')
    else:
        form = PacienteForm()
    return render(request, 'paciente_form.html', {'form': form})

@user_passes_test(es_personal_medico, login_url='login')
def paciente_editar(request, id_paciente):
    paciente = get_object_or_404(Paciente, id_paciente=id_paciente)
    if request.method == 'POST':
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            form.save()
            return redirect('pacientes_lista')
    else:
        form = PacienteForm(instance=paciente)
    return render(request, 'paciente_form.html', {'form': form, 'paciente': paciente})

@user_passes_test(es_medico_o_admin, login_url='login')
def paciente_eliminar(request, id_paciente):
    paciente = get_object_or_404(Paciente, id_paciente=id_paciente)
    if request.method == 'POST':
        paciente.delete()
        messages.success(request, 'Paciente eliminado exitosamente.')
        return redirect('pacientes_lista')
    return render(request, 'paciente_confirm_delete.html', {'paciente': paciente})

@login_required(login_url='login')
def historial_eliminar(request, id_historial):
    import os
    historial = get_object_or_404(HistorialClinico, id_historial=id_historial)
    
    if request.method == 'POST':
        try:
            # Intentar obtener la radiografía a través de las relaciones
            radiografia = None
            if historial.id_diagnostico and historial.id_diagnostico.id_resultado and historial.id_diagnostico.id_resultado.id_radiografia:
                radiografia = historial.id_diagnostico.id_resultado.id_radiografia
            
            # Si existe la radiografía, eliminarla (esto eliminará en cascada todo lo demás)
            if radiografia:
                if radiografia.ruta_archivo and os.path.exists(radiografia.ruta_archivo.path):
                    os.remove(radiografia.ruta_archivo.path)
                radiografia.delete()
                messages.success(request, 'Historial y registro completo eliminados exitosamente.')
            else:
                # Si por alguna razón no hay radiografía pero hay historial, eliminar solo el historial
                historial.delete()
                messages.success(request, 'Registro de historial eliminado exitosamente.')
                
        except Exception as e:
            messages.error(request, f'Error al eliminar: {str(e)}')
            
        # Redirigir de vuelta a la página anterior
        referer = request.META.get('HTTP_REFERER')
        if referer and 'pacientes/detalle' in referer:
            return redirect('paciente_detalle', id_paciente=historial.id_paciente.id_paciente)
        return redirect('pacientes_historial')
        
    return render(request, 'historial_confirm_delete.html', {'historial': historial})