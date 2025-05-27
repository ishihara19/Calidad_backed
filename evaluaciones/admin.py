from django.contrib import admin
from .models import Evaluacion, CalificacionCaracteristica, CalificacionSubCaracteristica

class CalificacionSubCaracteristicaInline(admin.TabularInline):
    model = CalificacionSubCaracteristica
    extra = 0
    readonly_fields = ['fecha_calificacion', 'porcentaje_obtenido']
    fields = [
        'subcaracteristica',
        'puntos',
        'puntos_maximo', 
        'porcentaje_obtenido',
        'observacion',
        'evidencia_url',
        'fecha_calificacion'
    ]

class CalificacionCaracteristicaInline(admin.StackedInline):
    model = CalificacionCaracteristica
    extra = 0
    readonly_fields = ['fecha_calificacion']
    fields = [
        'caracteristica',
        'puntuacion_obtenida',
        'puntuacion_maxima',
        'observaciones',
        'fecha_calificacion'
    ]

@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_evaluacion',
        'software',
        'norma', 
        'evaluador',
        'empresa',
        'estado',
        'puntuacion_total',
        'fecha_inicio',
        'fecha_completada'
    ]
    
    list_filter = [
        'estado',
        'norma',
        'empresa',
        'fecha_inicio',
        'fecha_completada'
    ]
    
    search_fields = [
        'codigo_evaluacion',
        'software__nombre',
        'norma__nombre',
        'evaluador__first_name',
        'evaluador__last_name',
        'empresa__nombre'
    ]
    
    readonly_fields = [
        'codigo_evaluacion',
        'fecha_inicio',
        'fecha_actualizacion',
        'puntuacion_total'
    ]
    
    fieldsets = (
        ('Información Principal', {
            'fields': (
                'codigo_evaluacion',
                'software',
                'norma',
                'evaluador',
                'empresa'
            )
        }),
        ('Estado y Fechas', {
            'fields': (
                'estado',
                'fecha_inicio',
                'fecha_completada',
                'fecha_actualizacion'
            )
        }),
        ('Resultados', {
            'fields': (
                'puntuacion_total',
                'observaciones_generales'
            )
        }),
    )
    
    inlines = [CalificacionCaracteristicaInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'software',
            'norma', 
            'evaluador',
            'empresa'
        )

@admin.register(CalificacionCaracteristica)
class CalificacionCaracteristicaAdmin(admin.ModelAdmin):
    list_display = [
        'evaluacion',
        'caracteristica',
        'puntuacion_obtenida',
        'puntuacion_maxima',
        'fecha_calificacion'
    ]
    
    list_filter = [
        'caracteristica',
        'fecha_calificacion',
        'evaluacion__estado'
    ]
    
    search_fields = [
        'evaluacion__codigo_evaluacion',
        'caracteristica__nombre'
    ]
    
    readonly_fields = ['fecha_calificacion']
    
    inlines = [CalificacionSubCaracteristicaInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'evaluacion',
            'caracteristica'
        )

@admin.register(CalificacionSubCaracteristica)
class CalificacionSubCaracteristicaAdmin(admin.ModelAdmin):
    list_display = [
        'get_evaluacion_codigo',
        'get_caracteristica_nombre',
        'subcaracteristica',
        'puntos',
        'porcentaje_obtenido',
        'fecha_calificacion'
    ]
    
    list_filter = [
        'puntos',
        'subcaracteristica__caracteristica',
        'fecha_calificacion'
    ]
    
    search_fields = [
        'calificacion_caracteristica__evaluacion__codigo_evaluacion',
        'subcaracteristica__nombre',
        'observacion'
    ]
    
    readonly_fields = [
        'fecha_calificacion',
        'porcentaje_obtenido'
    ]
    
    fieldsets = (
        ('Información Principal', {
            'fields': (
                'calificacion_caracteristica',
                'subcaracteristica'
            )
        }),
        ('Calificación', {
            'fields': (
                'puntos',
                'puntos_maximo',
                'porcentaje_obtenido'
            )
        }),
        ('Detalles', {
            'fields': (
                'observacion',
                'evidencia_url',
                'fecha_calificacion'
            )
        }),
    )
    
    def get_evaluacion_codigo(self, obj):
        return obj.calificacion_caracteristica.evaluacion.codigo_evaluacion
    get_evaluacion_codigo.short_description = 'Código Evaluación'
    get_evaluacion_codigo.admin_order_field = 'calificacion_caracteristica__evaluacion__codigo_evaluacion'
    
    def get_caracteristica_nombre(self, obj):
        return obj.calificacion_caracteristica.caracteristica.nombre
    get_caracteristica_nombre.short_description = 'Característica'
    get_caracteristica_nombre.admin_order_field = 'calificacion_caracteristica__caracteristica__nombre'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'calificacion_caracteristica__evaluacion',
            'calificacion_caracteristica__caracteristica',
            'subcaracteristica'
        )