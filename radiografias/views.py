from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from usuarios.decorators import es_personal_medico, es_medico_o_admin
from django.contrib import messages
from django.conf import settings
from .models import Radiografia
from pacientes.models import Paciente
import os
import time


@user_passes_test(es_medico_o_admin, login_url='login')
def nueva_carga_view(request):
    if request.method == 'POST':
        paciente_id = request.POST.get('paciente')
        archivo = request.FILES.get('archivo')
        if not paciente_id or not archivo:
            messages.error(request, 'Por favor seleccione un paciente y un archivo de radiografía.')
            return redirect('nueva_carga')
        
        paciente = get_object_or_404(Paciente, id_paciente=paciente_id)
        
        radiografia = Radiografia.objects.create(
            id_paciente=paciente,
            id_usuario=request.user,
            nombre_archivo=archivo.name,
            ruta_archivo=archivo,
            formato=os.path.splitext(archivo.name)[1].lower().replace('.', ''),
            estado_procesamiento='Completado'
        )
        
        # Procesar o crear el ResultadoIA con el modelo real (vía Subproceso)
        from diagnosticos.models import ResultadoIA
        import subprocess
        import re
        
        start_time = time.time()
        
        img_path = radiografia.ruta_archivo.path
        model_path = os.path.join(settings.BASE_DIR, 'ai_models', 'pneumonia_detection_model.h5')
        infer_script = os.path.join(settings.BASE_DIR, 'infer.py')
        
        # Ruta al Python global que contiene TensorFlow instalado en tu PC
        python_exe = r'C:\Users\HP\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe'
        
        try:
            result = subprocess.run([python_exe, infer_script, model_path, img_path], capture_output=True, text=True)
            output = result.stdout
            
            match = re.search(r'PROB:([0-9.]+)', output)
            if match:
                prob = float(match.group(1))
                prob_percent = round(prob * 100, 2)
                
                if prob >= 0.8:
                    prediccion = f"Neumonía detectada"
                elif (prob > 0.6 and prob < 0.8):
                    prediccion = f"Alta probabilidad de Neumonía"
                elif (prob > 0.4 and prob < 0.6):
                    prediccion = f"Neumonía en etapa leve"
                else:
                    prediccion = f"Normal"
            else:
                prob_percent = 0.0
                prediccion = f"Modelo no disponible (Error interno)"
                print(f"Fallo IA: {result.stderr}")
        except Exception as e:
            prob_percent = 0.0
            prediccion = f"Modelo no disponible ({e})"
            
        tiempo_procesamiento = round(time.time() - start_time, 2)
        
        ResultadoIA.objects.create(
            id_radiografia=radiografia,
            prediccion=prediccion,
            porcentaje_confianza=prob_percent,
            mapa_calor='grad_cam_mock.png', # Placeholder
            tiempo_procesamiento=tiempo_procesamiento,
            modelo_ia='TensorFlow Custom CNN'
        )
        
        messages.success(request, 'Radiografía subida y procesada por IA con éxito.')
        return redirect('resultado_ia_detalle', id_radiografia=radiografia.id_radiografia)
        
    pacientes = Paciente.objects.all().order_by('apellidos', 'nombres')
    return render(request, 'nueva_carga.html', {'pacientes': pacientes})

@user_passes_test(es_personal_medico, login_url='login')
def lista_radiografias(request, id_paciente):
    paciente = get_object_or_404(Paciente, id_paciente=id_paciente)
    radiografias = Radiografia.objects.filter(id_paciente=paciente).order_by('-fecha_subida')
    return render(request, 'lista_radiografias.html', {'paciente': paciente, 'radiografias': radiografias})

@user_passes_test(es_medico_o_admin, login_url='login')
def radiografia_eliminar(request, id_radiografia):
    radiografia = get_object_or_404(Radiografia, id_radiografia=id_radiografia)
    paciente_id = radiografia.id_paciente.id_paciente
    if request.method == 'POST':
        # Eliminar el archivo físico si existe
        if radiografia.ruta_archivo:
            if os.path.exists(radiografia.ruta_archivo.path):
                os.remove(radiografia.ruta_archivo.path)
        radiografia.delete()
        messages.success(request, 'Radiografía eliminada exitosamente.')
        return redirect('lista_radiografias', id_paciente=paciente_id)
    return render(request, 'radiografia_confirm_delete.html', {'radiografia': radiografia})