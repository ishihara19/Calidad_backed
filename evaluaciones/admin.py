from django.contrib import admin
from .models import Evaluacion, CalificacionCaracteristica, CalificacionSubCaracteristica
from django.utils.html import format_html
from django.db.models import Sum
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
    extra = 1
    readonly_fields = ['fecha_calificacion', 'puntuacion_obtenida']
    fields = [
        'caracteristica',
        'porcentaje_asignado',  # NUEVO CAMPO
        'puntuacion_obtenida',
        'puntuacion_maxima',
        'observaciones',
        'fecha_calificacion'
    ]
    class Media:
        js = ('js/validacion_porcentaje.js',)  # La ruta relativa dentro de static/
     # Mostrar el total dinámico debajo del inline (con JS también puedes hacerlo en tiempo real)
    def get_extra(self, request, obj=None, **kwargs):
        return 0  # Evitar filas vacías que confunden el cálculo

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
        'suma_porcentajes_display',  # NUEVO
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
        'puntuacion_total',
        'suma_porcentajes_display'
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
                'suma_porcentajes_display',
                'observaciones_generales'
            )
        }),
    )
    
    inlines = [CalificacionCaracteristicaInline]
    
    def suma_porcentajes_display(self, obj):
        """Mostrar la suma de porcentajes asignados"""
        total = sum(cal.porcentaje_asignado for cal in obj.calificaciones_caracteristica.all())
        color = 'green' if abs(total - 100) < 0.01 else 'red'
        return f'<span style="color: {color}; font-weight: bold;">{total}%</span>'
    
    suma_porcentajes_display.short_description = 'Suma Porcentajes'
    suma_porcentajes_display.allow_tags = True
    
    def mostrar_porcentaje_total(self, obj):
        total = obj.calificaciones_caracteristica.aggregate(
            total=Sum('porcentaje_asignado')
        )['total'] or 0

        color = "red" if total > 100 else ("orange" if total < 100 else "green")
        return format_html('<strong style="color:{};">{}%</strong>', color, round(total, 2))
    
    mostrar_porcentaje_total.short_description = "Total % asignado"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'software',
            'norma', 
            'evaluador',
            'empresa'
        ).prefetch_related(
            'calificaciones_caracteristica'
        )

@admin.register(CalificacionCaracteristica)
class CalificacionCaracteristicaAdmin(admin.ModelAdmin):
    list_display = [
        'evaluacion',
        'caracteristica',
        'porcentaje_asignado',  # NUEVO CAMPO
        'puntuacion_obtenida',
        'puntuacion_maxima',
        'numero_subcaracteristicas_evaluadas',  # NUEVO
        'fecha_calificacion'
    ]
    
    list_filter = [
        'caracteristica',
        'fecha_calificacion',
        'evaluacion__estado',
        'evaluacion__empresa'
    ]
    
    search_fields = [
        'evaluacion__codigo_evaluacion',
        'caracteristica__nombre',
        'evaluacion__software__nombre'
    ]
    
    readonly_fields = [
        'fecha_calificacion',
        'puntuacion_obtenida',
        'numero_subcaracteristicas_evaluadas'
    ]
    
    fieldsets = (
        ('Información Principal', {
            'fields': (
                'evaluacion',
                'caracteristica'
            )
        }),
        ('Asignación de Peso', {
            'fields': (
                'porcentaje_asignado',
            ),
            'description': 'El porcentaje asignado a esta característica en esta evaluación específica'
        }),
        ('Resultados', {
            'fields': (
                'puntuacion_obtenida',
                'puntuacion_maxima',
                'numero_subcaracteristicas_evaluadas'
            )
        }),
        ('Observaciones', {
            'fields': (
                'observaciones',
                'fecha_calificacion'
            )
        }),
    )
    
    inlines = [CalificacionSubCaracteristicaInline]
    
    def numero_subcaracteristicas_evaluadas(self, obj):
        """Mostrar número de subcaracterísticas evaluadas"""
        count = obj.calificaciones_subcaracteristica.count()
        total_disponibles = obj.caracteristica.subcaracteristicas.count()
        return f"{count} de {total_disponibles}"
    
    numero_subcaracteristicas_evaluadas.short_description = 'Subcaracterísticas Evaluadas'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'evaluacion',
            'caracteristica'
        ).prefetch_related(
            'calificaciones_subcaracteristica'
        )

@admin.register(CalificacionSubCaracteristica)
class CalificacionSubCaracteristicaAdmin(admin.ModelAdmin):
    list_display = [
        'get_evaluacion_codigo',
        'get_caracteristica_nombre',
        'subcaracteristica',
        'puntos',
        'puntos_maximo',
        'porcentaje_obtenido',
        'tiene_evidencia',  # NUEVO
        'fecha_calificacion'
    ]
    
    list_filter = [
        'puntos',
        'subcaracteristica__caracteristica',
        'fecha_calificacion',
        'calificacion_caracteristica__evaluacion__empresa'
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
    
    def tiene_evidencia(self, obj):
        """Indicar si tiene URL de evidencia"""
        if obj.evidencia_url:
            return f'<a href="{obj.evidencia_url}" target="_blank">📎 Ver</a>'
        return '❌ No'
    
    tiene_evidencia.short_description = 'Evidencia'
    tiene_evidencia.allow_tags = True
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'calificacion_caracteristica__evaluacion',
            'calificacion_caracteristica__caracteristica',
            'subcaracteristica'
        )

# ACCIONES PERSONALIZADAS PARA EL ADMIN

@admin.action(description='Recalcular puntuaciones de evaluaciones seleccionadas')
def recalcular_puntuaciones(modeladmin, request, queryset):
    """Acción para recalcular las puntuaciones de evaluaciones"""
    from django.db import transaction
    
    actualizadas = 0
    for evaluacion in queryset:
        try:
            with transaction.atomic():
                # Recalcular puntuaciones de características
                for cal_car in evaluacion.calificaciones_caracteristica.all():
                    cal_car.puntuacion_obtenida = cal_car.calcular_puntuacion_caracteristica()
                    cal_car.save()
                
                # Recalcular puntuación total
                evaluacion.puntuacion_total = evaluacion.calcular_puntuacion_total()
                evaluacion.save()
                
                actualizadas += 1
        except Exception as e:
            modeladmin.message_user(
                request,
                f"Error al recalcular {evaluacion.codigo_evaluacion}: {e}",
                level='ERROR'
            )
    
    if actualizadas > 0:
        modeladmin.message_user(
            request,
            f"Se recalcularon {actualizadas} evaluaciones exitosamente.",
            level='SUCCESS'
        )

@admin.action(description='Validar porcentajes de evaluaciones seleccionadas')
def validar_porcentajes_evaluaciones(modeladmin, request, queryset):
    """Acción para validar que los porcentajes sumen 100%"""
    problemas = []
    
    for evaluacion in queryset:
        total_porcentaje = sum(
            cal.porcentaje_asignado for cal in evaluacion.calificaciones_caracteristica.all()
        )
        
        if abs(total_porcentaje - 100) > 0.01:
            problemas.append(f"{evaluacion.codigo_evaluacion}: {total_porcentaje}%")
    
    if problemas:
        modeladmin.message_user(
            request,
            f"Evaluaciones con porcentajes incorrectos: {', '.join(problemas)}",
            level='WARNING'
        )
    else:
        modeladmin.message_user(
            request,
            "Todas las evaluaciones seleccionadas tienen porcentajes correctos (100%)",
            level='SUCCESS'
        )

@admin.action(description='Marcar como completadas')
def marcar_completadas(modeladmin, request, queryset):
    """Acción para marcar evaluaciones como completadas"""
    from datetime import datetime
    
    actualizadas = 0
    for evaluacion in queryset:
        if evaluacion.estado != 'completada':
            # Validar que tenga calificaciones
            if evaluacion.calificaciones_caracteristica.exists():
                evaluacion.estado = 'completada'
                evaluacion.fecha_completada = datetime.now()
                evaluacion.save()
                actualizadas += 1
    
    if actualizadas > 0:
        modeladmin.message_user(
            request,
            f"Se marcaron {actualizadas} evaluaciones como completadas.",
            level='SUCCESS'
        )

# Agregar las acciones a EvaluacionAdmin
EvaluacionAdmin.actions = [
    recalcular_puntuaciones,
    validar_porcentajes_evaluaciones,
    marcar_completadas
]

# REGISTRO DE FILTROS PERSONALIZADOS

class PorcentajeValidoFilter(admin.SimpleListFilter):
    """Filtro para mostrar evaluaciones con porcentajes válidos/inválidos"""
    title = 'Porcentajes válidos'
    parameter_name = 'porcentajes_validos'
    
    def lookups(self, request, model_admin):
        return (
            ('si', 'Sí (suman 100%)'),
            ('no', 'No (no suman 100%)'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'si':
            # Filtrar evaluaciones donde los porcentajes suman 100% (±0.01)
            evaluaciones_validas = []
            for evaluacion in queryset:
                total = sum(cal.porcentaje_asignado for cal in evaluacion.calificaciones_caracteristica.all())
                if abs(total - 100) <= 0.01:
                    evaluaciones_validas.append(evaluacion.id)
            return queryset.filter(id__in=evaluaciones_validas)
        
        elif self.value() == 'no':
            # Filtrar evaluaciones donde los porcentajes NO suman 100%
            evaluaciones_invalidas = []
            for evaluacion in queryset:
                total = sum(cal.porcentaje_asignado for cal in evaluacion.calificaciones_caracteristica.all())
                if abs(total - 100) > 0.01:
                    evaluaciones_invalidas.append(evaluacion.id)
            return queryset.filter(id__in=evaluaciones_invalidas)
        
        return queryset

class PuntuacionRangoFilter(admin.SimpleListFilter):
    """Filtro para agrupar evaluaciones por rango de puntuación"""
    title = 'Rango de puntuación'
    parameter_name = 'rango_puntuacion'
    
    def lookups(self, request, model_admin):
        return (
            ('excelente', 'Excelente (90-100%)'),
            ('bueno', 'Bueno (70-89%)'),
            ('regular', 'Regular (50-69%)'),
            ('deficiente', 'Deficiente (0-49%)'),
            ('sin_puntuar', 'Sin puntuar'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'excelente':
            return queryset.filter(puntuacion_total__gte=90, puntuacion_total__lte=100)
        elif self.value() == 'bueno':
            return queryset.filter(puntuacion_total__gte=70, puntuacion_total__lt=90)
        elif self.value() == 'regular':
            return queryset.filter(puntuacion_total__gte=50, puntuacion_total__lt=70)
        elif self.value() == 'deficiente':
            return queryset.filter(puntuacion_total__gte=0, puntuacion_total__lt=50)
        elif self.value() == 'sin_puntuar':
            return queryset.filter(puntuacion_total__isnull=True)
        return queryset

# Agregar los filtros personalizados
EvaluacionAdmin.list_filter = EvaluacionAdmin.list_filter + [
    PorcentajeValidoFilter,
    PuntuacionRangoFilter
]