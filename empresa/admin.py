from django.contrib import admin
from .models import Empresa

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'nit', 'email', 'telefono', 'fecha_creacion')
    list_filter = ('fecha_creacion',)
    search_fields = ('nombre', 'nit', 'email')
    ordering = ('-fecha_creacion',)
    readonly_fields = ('id', 'fecha_creacion')

    fieldsets = (
        ('Información general', {
            'fields': ('id', 'nombre', 'nit', 'direccion', 'email', 'telefono')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion',)
        }),
    )