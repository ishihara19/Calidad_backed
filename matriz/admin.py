from django.contrib import admin
from .models import (
    Riesgos, Procesos, TipoRiesgos, RiesgoAsociados, PosibleOcurrencia,
    Impacto, OpcionTratamiento, Matriz
)

# Modelo base de solo lectura
class ReadOnlyAdmin(admin.ModelAdmin):
    readonly_fields = ['id']

@admin.register(Riesgos)
class RiesgosAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Procesos)
class ProcesosAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre', 'descripcion')

@admin.register(TipoRiesgos)
class TipoRiesgosAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(RiesgoAsociados)
class RiesgoAsociadosAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(PosibleOcurrencia)
class PosibleOcurrenciaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'valor')
    search_fields = ('nombre',)
    list_filter = ('valor',)

@admin.register(Impacto)
class ImpactoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'valor')
    search_fields = ('nombre',)
    list_filter = ('valor',)

@admin.register(OpcionTratamiento)
class OpcionTratamientoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Matriz)
class MatrizAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'fecha_riesgo', 'riesgo', 'zona_riego', 'aceptado')
    search_fields = ('id', 'codigo_riesgo', 'descripcion', 'usuario__username')
    list_filter = ('zona_riego', 'aceptado', 'tipo_impacto', 'riesgo_afectacion')
    raw_id_fields = ('user', 'riesgo', 'proceso', 'Posibilidad_ocurrencia', 'impacto', 'opcion_tratamiento')
    filter_horizontal = ('riesgo_asociados',)
