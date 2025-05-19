from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Caracteristica,
    Subcaracteristica,
    Pregunta,
    Proyecto,
    Evaluacion,
    RespuestaPregunta
)

class SubcaracteristicaInline(admin.TabularInline):
    model = Subcaracteristica
    extra = 1
    show_change_link = True

@admin.register(Caracteristica)
class CaracteristicaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre')
    search_fields = ('codigo', 'nombre', 'descripcion')
    inlines = (SubcaracteristicaInline,)
    ordering = ('codigo',)

class PreguntaInline(admin.TabularInline):
    model = Pregunta
    extra = 1
    show_change_link = True

@admin.register(Subcaracteristica)
class SubcaracteristicaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'caracteristica')
    list_filter = ('caracteristica',)
    search_fields = ('codigo', 'nombre', 'descripcion')
    inlines = (PreguntaInline,)
    ordering = ('caracteristica__codigo', 'codigo')

@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'texto_corto', 'subcaracteristica')
    list_filter = ('subcaracteristica__caracteristica', 'subcaracteristica')
    search_fields = ('codigo', 'texto')
    ordering = ('subcaracteristica__caracteristica__codigo', 'subcaracteristica__codigo', 'codigo')

    def texto_corto(self, obj):
        return obj.texto[:100] + '...' if len(obj.texto) > 100 else obj.texto
    texto_corto.short_description = 'Texto'

class EvaluacionInline(admin.TabularInline):
    model = Evaluacion
    extra = 0
    show_change_link = True

@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'propietario', 'fecha_creacion', 'contar_evaluaciones')
    list_filter = ('propietario', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    date_hierarchy = 'fecha_creacion'
    inlines = (EvaluacionInline,)

    def contar_evaluaciones(self, obj):
        count = obj.evaluaciones.count()
        return count
    contar_evaluaciones.short_description = 'Evaluaciones'

class RespuestaPreguntaInline(admin.TabularInline):
    model = RespuestaPregunta
    extra = 0
    show_change_link = True
    readonly_fields = ('mostrar_evidencia',)
    fields = ('pregunta', 'valor', 'observacion', 'evidencia', 'mostrar_evidencia')

    def mostrar_evidencia(self, obj):
        if obj.evidencia:
            return format_html('<a href="{}" target="_blank">Ver evidencia</a>', obj.evidencia.url)
        return '-'
    mostrar_evidencia.short_description = 'Ver'

@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'proyecto', 'evaluador', 'estado', 'fecha_creacion', 'porcentaje_cumplimiento', 'nivel_cumplimiento')
    list_filter = ('estado', 'evaluador', 'proyecto')
    search_fields = ('proyecto__nombre', 'evaluador__username')
    date_hierarchy = 'fecha_creacion'
    inlines = (RespuestaPreguntaInline,)
    readonly_fields = ('porcentaje_cumplimiento', 'nivel_cumplimiento_display')

    def porcentaje_cumplimiento(self, obj):
        return f"{obj.calcular_porcentaje_total():.2f}%"
    porcentaje_cumplimiento.short_description = 'Porcentaje'

    def nivel_cumplimiento(self, obj):
        nivel = obj.obtener_nivel_cumplimiento()
        niveles = {
            0: '❌ No cumple',
            1: '⚠️ Cumple parcialmente',
            2: '✅ Cumple mayormente',
            3: '🌟 Cumple totalmente'
        }
        return niveles.get(nivel, 'Desconocido')
    nivel_cumplimiento.short_description = 'Nivel'

    def nivel_cumplimiento_display(self, obj):
        nivel = obj.obtener_nivel_cumplimiento()
        porcentaje = obj.calcular_porcentaje_total()
        niveles = {
            0: f'❌ No cumple ({porcentaje:.2f}% - Nivel 0)',
            1: f'⚠️ Cumple parcialmente ({porcentaje:.2f}% - Nivel 1)',
            2: f'✅ Cumple mayormente ({porcentaje:.2f}% - Nivel 2)',
            3: f'🌟 Cumple totalmente ({porcentaje:.2f}% - Nivel 3)'
        }
        return niveles.get(nivel, 'Desconocido')
    nivel_cumplimiento_display.short_description = 'Nivel de Cumplimiento'

@admin.register(RespuestaPregunta)
class RespuestaPreguntaAdmin(admin.ModelAdmin):
    list_display = ('id', 'evaluacion', 'pregunta_codigo', 'pregunta_texto_corto', 'valor', 'tiene_evidencia')
    list_filter = ('evaluacion__proyecto', 'evaluacion', 'valor')
    search_fields = ('pregunta__texto', 'observacion', 'evaluacion__proyecto__nombre')
    readonly_fields = ('mostrar_evidencia',)

    def pregunta_codigo(self, obj):
        return obj.pregunta.codigo
    pregunta_codigo.short_description = 'Código'

    def pregunta_texto_corto(self, obj):
        texto = obj.pregunta.texto
        return texto[:100] + '...' if len(texto) > 100 else texto
    pregunta_texto_corto.short_description = 'Pregunta'

    def tiene_evidencia(self, obj):
        return bool(obj.evidencia)
    tiene_evidencia.boolean = True
    tiene_evidencia.short_description = 'Evidencia'

    def mostrar_evidencia(self, obj):
        if obj.evidencia:
            return format_html('<a href="{}" target="_blank">Ver evidencia</a>', obj.evidencia.url)
        return 'Sin evidencia'
    mostrar_evidencia.short_description = 'Evidencia'