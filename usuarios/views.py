from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, get_user_model
from django.contrib.auth.decorators import user_passes_test
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from django.db.models import Q
from django.utils import timezone
from .models import HistorialAcceso, Rol, Usuario
from django.contrib.auth import logout as auth_logout


def obtener_ip_cliente(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def obtener_sistema_operativo(user_agent):
    user_agent = user_agent.lower()
    if 'windows' in user_agent:
        return 'Windows'
    if 'android' in user_agent:
        return 'Android'
    if 'iphone' in user_agent or 'ipad' in user_agent:
        return 'iOS'
    if 'mac os' in user_agent:
        return 'macOS'
    if 'linux' in user_agent:
        return 'Linux'
    return 'Desconocido'

def login(request):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())
    user_model = get_user_model()
    error = None
    if request.method == 'POST':
        # Validar el CAPTCHA
        try:
            captcha.clean(request.POST.get('g-recaptcha-response'))
        except Exception:
            error = 'Por favor, resuelva el CAPTCHA para continuar.'
            return render(request, 'login.html', {
                'captcha': captcha.widget.render('g-recaptcha-response', None),
                'error': error,
            })
        
        # Obtener los datos del formulario (ahora aceptamos username o email)
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        
        if not username or not password:
            error = 'Usuario/Correo y contraseña son obligatorios.'
            return render(request, 'login.html', {
                'captcha': captcha.widget.render('g-recaptcha-response', None),
                'error': error,
            })

        try:
            db_user = user_model.objects.filter(Q(username=username) | Q(email=username)).first()
        except Exception:
            db_user = None

        if db_user is None:
            error = 'Ese usuario no existe o la contraseña es incorrecta.'
            return render(request, 'login.html', {
                'captcha': captcha.widget.render('g-recaptcha-response', None),
                'error': error,
            })

        user = authenticate(request, username=db_user.username, password=password)
        if user is None:
            error = 'Ese usuario no existe o la contraseña es incorrecta.'
            return render(request, 'login.html', {
                'captcha': captcha.widget.render('g-recaptcha-response', None),
                'error': error,
            })

        auth_login(request, user)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        HistorialAcceso.objects.create(
            id_usuario=user,
            ip_acceso=obtener_ip_cliente(request),
            navegador=user_agent[:100],
            sistema_operativo=obtener_sistema_operativo(user_agent),
        )
        user.ultimo_acceso = timezone.now()
        user.save(update_fields=['ultimo_acceso'])
        messages.success(request, f'¡Bienvenido de nuevo, {user.username}!')
        return redirect('panel_principal')
    
    # Si es GET, mostrar el formulario vacio
    return render(request, 'login.html', {
        'captcha': captcha.widget.render('g-recaptcha-response', None),
        'error': error,
    })


def registro(request):
    error = None
    if request.method == 'POST':
        nombres = request.POST.get('nombres', '').strip()
        apellidos = request.POST.get('apellidos', '').strip()
        ci = request.POST.get('ci', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        id_rol_str = request.POST.get('id_rol', '')

        if not all([nombres, apellidos, ci, email, password, confirm_password, id_rol_str]):
            error = 'Por favor complete todos los campos obligatorios.'
        elif password != confirm_password:
            error = 'Las contraseñas no coinciden.'
        else:
            # Generar username: primer nombre + inicial del primer apellido + ci
            primer_nombre = nombres.split()[0].lower() if nombres else ''
            primera_letra_apellido = apellidos.split()[0][0].lower() if apellidos else ''
            username = f"{primer_nombre}{primera_letra_apellido}{ci}"

            if Usuario.objects.filter(username=username).exists():
                error = 'Ya existe un usuario registrado con esa información.'
            elif Usuario.objects.filter(email=email).exists():
                error = 'Ya existe un usuario con ese correo electrónico.'
            else:
                try:
                    rol = Rol.objects.get(id_rol=int(id_rol_str))
                    user = Usuario.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        nombres=nombres,
                        apellidos=apellidos,
                        ci=ci,
                        telefono=telefono,
                        id_rol=rol
                    )
                    # Iniciar sesión automáticamente después de registrarse
                    auth_login(request, user)
                    messages.success(request, 'Usuario registrado exitosamente. ¡Bienvenido!')
                    return redirect('panel_principal')
                except Rol.DoesNotExist:
                    error = 'El rol seleccionado no es válido.'
                except Exception as e:
                    error = f'Error al registrar: {str(e)}'

    roles = Rol.objects.filter(estado=True)
    return render(request, 'reguistro.html', {'roles': roles, 'error': error})



#cerrar sesion 
def cerrar_sesion(request):
    auth_logout(request)
    return redirect('login')


# --- GESTIÓN DE USUARIOS (RF-11) ---

def es_administrador(user):
    return user.is_authenticated and user.id_rol and user.id_rol.nombre == 'Administrador'

@user_passes_test(es_administrador, login_url='login')
def lista_usuarios(request):
    usuarios = Usuario.objects.all().order_by('-fecha_creacion')
    return render(request, 'usuarios/lista_usuarios.html', {'usuarios': usuarios})


@user_passes_test(es_administrador, login_url='login')
def historial_accesos(request):
    accesos = HistorialAcceso.objects.select_related(
        'id_usuario',
        'id_usuario__id_rol',
    ).order_by('-fecha_acceso')
    return render(request, 'usuarios/historial_accesos.html', {'accesos': accesos})


@user_passes_test(es_administrador, login_url='login')
def crear_usuario(request):
    error = None
    if request.method == 'POST':
        nombres = request.POST.get('nombres', '').strip()
        apellidos = request.POST.get('apellidos', '').strip()
        ci = request.POST.get('ci', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        id_rol_str = request.POST.get('id_rol', '')
        estado = request.POST.get('estado') == 'on'

        if not all([nombres, apellidos, ci, email, password, confirm_password, id_rol_str]):
            error = 'Por favor complete todos los campos obligatorios.'
        elif password != confirm_password:
            error = 'Las contraseñas no coinciden.'
        else:
            primer_nombre = nombres.split()[0].lower() if nombres else ''
            primera_letra_apellido = apellidos.split()[0][0].lower() if apellidos else ''
            username = f"{primer_nombre}{primera_letra_apellido}{ci}"

            if Usuario.objects.filter(username=username).exists():
                error = 'Ya existe un usuario con ese nombre de usuario generado.'
            elif Usuario.objects.filter(email=email).exists():
                error = 'Ya existe un usuario con ese correo electrónico.'
            else:
                try:
                    rol = Rol.objects.get(id_rol=int(id_rol_str))
                    user = Usuario.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        nombres=nombres,
                        apellidos=apellidos,
                        ci=ci,
                        telefono=telefono,
                        id_rol=rol
                    )
                    user.estado = estado
                    user.save()
                    return redirect('lista_usuarios')
                except Rol.DoesNotExist:
                    error = 'El rol seleccionado no es válido.'
                except Exception as e:
                    error = f'Error al registrar: {str(e)}'

    roles = Rol.objects.filter(estado=True)
    return render(request, 'usuarios/formulario_usuario.html', {
        'roles': roles, 
        'error': error,
        'accion': 'Crear'
    })


@user_passes_test(es_administrador, login_url='login')
def editar_usuario(request, id):
    error = None
    usuario = get_object_or_404(Usuario, pk=id)

    if request.method == 'POST':
        nombres = request.POST.get('nombres', '').strip()
        apellidos = request.POST.get('apellidos', '').strip()
        ci = request.POST.get('ci', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        id_rol_str = request.POST.get('id_rol', '')
        estado = request.POST.get('estado') == 'on'

        if not all([nombres, apellidos, ci, email, id_rol_str]):
            error = 'Por favor complete todos los campos obligatorios.'
        else:
            # Check unique email but exclude the current user
            if Usuario.objects.filter(email=email).exclude(pk=id).exists():
                error = 'Ya existe otro usuario con ese correo electrónico.'
            else:
                try:
                    rol = Rol.objects.get(id_rol=int(id_rol_str))
                    usuario.nombres = nombres
                    usuario.apellidos = apellidos
                    usuario.ci = ci
                    usuario.telefono = telefono
                    usuario.email = email
                    usuario.id_rol = rol
                    usuario.estado = estado
                    
                    if password:
                        usuario.set_password(password)
                        
                    usuario.save()
                    return redirect('lista_usuarios')
                except Rol.DoesNotExist:
                    error = 'El rol seleccionado no es válido.'
                except Exception as e:
                    error = f'Error al actualizar: {str(e)}'

    roles = Rol.objects.filter(estado=True)
    return render(request, 'usuarios/formulario_usuario.html', {
        'roles': roles, 
        'error': error,
        'usuario': usuario,
        'accion': 'Editar'
    })


@user_passes_test(es_administrador, login_url='login')
def eliminar_usuario(request, id):
    usuario = get_object_or_404(Usuario, pk=id)
    if request.method == 'POST':
        usuario.delete()
        return redirect('lista_usuarios')
    
    return render(request, 'usuarios/eliminar_usuario.html', {'usuario': usuario})


# --- GESTIÓN DE ROLES (RF-11) ---

@user_passes_test(es_administrador, login_url='login')
def lista_roles(request):
    roles = Rol.objects.all().order_by('nombre')
    return render(request, 'usuarios/lista_roles.html', {'roles': roles})


@user_passes_test(es_administrador, login_url='login')
def crear_rol(request):
    error = None
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        estado = request.POST.get('estado') == 'on'

        if not nombre:
            error = 'El nombre del rol es obligatorio.'
        elif Rol.objects.filter(nombre=nombre).exists():
            error = 'Ya existe un rol con ese nombre.'
        else:
            Rol.objects.create(nombre=nombre, descripcion=descripcion, estado=estado)
            return redirect('lista_roles')

    return render(request, 'usuarios/formulario_rol.html', {
        'error': error,
        'accion': 'Crear'
    })


@user_passes_test(es_administrador, login_url='login')
def editar_rol(request, id_rol):
    rol = get_object_or_404(Rol, id_rol=id_rol)
    error = None
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        estado = request.POST.get('estado') == 'on'

        if not nombre:
            error = 'El nombre del rol es obligatorio.'
        elif Rol.objects.filter(nombre=nombre).exclude(id_rol=id_rol).exists():
            error = 'Ya existe otro rol con ese nombre.'
        else:
            rol.nombre = nombre
            rol.descripcion = descripcion
            rol.estado = estado
            rol.save()
            return redirect('lista_roles')

    return render(request, 'usuarios/formulario_rol.html', {
        'rol': rol,
        'error': error,
        'accion': 'Editar'
    })


@user_passes_test(es_administrador, login_url='login')
def eliminar_rol(request, id_rol):
    rol = get_object_or_404(Rol, id_rol=id_rol)
    if request.method == 'POST':
        # Verificar que no haya usuarios asignados a este rol
        if rol.usuario_set.exists():
            return render(request, 'usuarios/eliminar_rol.html', {
                'rol': rol,
                'error': 'No se puede eliminar este rol porque tiene usuarios asignados.'
            })
        rol.delete()
        return redirect('lista_roles')
    return render(request, 'usuarios/eliminar_rol.html', {'rol': rol})
