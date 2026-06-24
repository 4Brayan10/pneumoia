from django.contrib.auth.decorators import user_passes_test

def es_administrador(user):
    return user.is_authenticated and user.id_rol and user.id_rol.nombre == 'Administrador'

def es_medico(user):
    return user.is_authenticated and user.id_rol and user.id_rol.nombre == 'Médico'

def es_enfermera(user):
    return user.is_authenticated and user.id_rol and user.id_rol.nombre == 'Enfermera'

def es_medico_o_admin(user):
    return user.is_authenticated and user.id_rol and user.id_rol.nombre in ['Médico', 'Administrador']

def es_personal_medico(user):
    return user.is_authenticated and user.id_rol and user.id_rol.nombre in ['Médico', 'Enfermera', 'Administrador']
