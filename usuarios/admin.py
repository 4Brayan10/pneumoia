from django.contrib import admin
from .models import Rol, Usuario, HistorialAcceso
# Register your models here.

admin.site.register(Rol)
admin.site.register(Usuario)
admin.site.register(HistorialAcceso)