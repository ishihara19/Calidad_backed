from django.contrib import admin
from .models import Software

@admin.register(Software)
class SoftwareAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nombre',
        'empresa',
        'vesion',
        'fecha_registro',
        'fecha_actualizacion',
        'codigo_software',
    )
    search_fields = ('nombre', 'empresa__nombre', 'codigo_software')
    list_filter = ('empresa', 'fecha_registro')
    readonly_fields = ('fecha_registro', 'fecha_actualizacion')
    ordering = ('-fecha_registro',)
    fieldsets = (
        (None, {
            'fields': (
                'empresa',
                'nombre',
                'vesion',
                'codigo_software',
                'url',
            )
        }),
        ('Objetivos', {
            'fields': (
                'objectivo_general',
                'objetivo_especifico',
            )
        }),
        ('Fechas', {
            'fields': (
                'fecha_registro',
                'fecha_actualizacion',
            )
        }),
    )
