# matriz/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import MatrizRiesgo, RiesgoMatriz, CausaRiesgo, ParametroMatriz, AuditoriaMatriz

class CausaRiesgoInline(admin.TabularInline):
    model = CausaRiesgo
    extra = 1
    fields = ['orden', 'causa', 'factor', 'controles']
    ordering = ['orden']

class RiesgoMatrizInline(admin.StackedInline):
    model = RiesgoMatriz
    extra = 0
    fields = [
        ('numero', 'codigo', 'fecha'),
        'nombre',
        'descripcion',
        'tipo_riesgo',
        ('probabilidad', 'impacto'),
        'controles_existentes',
        ('tipo_control', 'efectividad_control'),
        'tratamiento',
        'responsable_control',
        'aceptado'
    ]
    readonly_fields = ['zona_riesgo_display']
    
    def zona_riesgo_display(self, obj):
        if obj.id:
            zona = obj.calcular_zona_riesgo()
            color_map = {
                'EXTREMA': '#dc2626',
                'ALTA': '#ea580c', 
                'MODERADA': '#ca8a04',
                'BAJA': '#16a34a',
                'MUY BAJA': '#059669'
            }
            color = color_map.get(zona['nivel'], '#6b7280')
            return format_html(
                '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">'
                '{} ({})</span>',
                color, zona['nivel'], zona['valor']
            )
        return "N/A"
    zona_riesgo_display.short_description = 'Zona de Riesgo'

@admin.register(MatrizRiesgo)
class MatrizRiesgoAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'nombre', 
        'empresa',
        'responsable',
        'creado_por',
        'total_riesgos_display',
        'resumen_niveles_display',
        'fecha_creacion',
        'fecha_modificacion'
    ]
    
    list_filter = [
        'empresa',
        'fecha_creacion',
        'fecha_modificacion',
        'creado_por'
    ]
    
    search_fields = [
        'nombre',
        'descripcion', 
        'responsable',
        'empresa__nombre',
        'creado_por__first_name',
        'creado_por__last_name'
    ]
    
    readonly_fields = [
        'id',
        'fecha_modificacion',
        'total_riesgos_display',
        'resumen_niveles_display'
    ]
    
    fieldsets = (
        ('Información Principal', {
            'fields': (
                'id',
                'nombre',
                'descripcion',
                'empresa'
            )
        }),
        ('Responsabilidad', {
            'fields': (
                'responsable',
                'creado_por'
            )
        }),
        ('Fechas', {
            'fields': (
                'fecha_creacion',
                'fecha_modificacion'
            )
        }),
        ('Estadísticas', {
            'fields': (
                'total_riesgos_display',
                'resumen_niveles_display'
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [RiesgoMatrizInline]
    
    def total_riesgos_display(self, obj):
        return obj.total_riesgos
    total_riesgos_display.short_description = 'Total de Riesgos'
    
    def resumen_niveles_display(self, obj):
        resumen = obj.resumen_riesgos_por_nivel
        html_parts = []
        
        color_map = {
            'EXTREMA': '#dc2626',
            'ALTA': '#ea580c',
            'MODERADA': '#ca8a04', 
            'BAJA': '#16a34a',
            'MUY_BAJA': '#059669'
        }
        
        for nivel, count in resumen.items():
            if count > 0:
                color = color_map.get(nivel, '#6b7280')
                html_parts.append(
                    f'<span style="background-color: {color}; color: white; '
                    f'padding: 2px 6px; border-radius: 3px; margin-right: 4px; font-size: 11px;">'
                    f'{nivel.replace("_", " ")}: {count}</span>'
                )
        
        return format_html(' '.join(html_parts)) if html_parts else 'Sin riesgos'
    resumen_niveles_display.short_description = 'Distribución por Nivel'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'empresa', 'creado_por'
        ).prefetch_related('riesgos')

@admin.register(RiesgoMatriz)
class RiesgoMatrizAdmin(admin.ModelAdmin):
    list_display = [
        'matriz',
        'numero',
        'codigo',
        'nombre',
        'tipo_riesgo',
        'probabilidad',
        'impacto',
        'zona_riesgo_display',
        'efectividad_control',
        'aceptado_display'
    ]
    
    list_filter = [
        'matriz__empresa',
        'matriz',
        'tipo_riesgo',
        'probabilidad',
        'impacto',
        'tipo_control',
        'aceptado',
        'fecha'
    ]
    
    search_fields = [
        'nombre',
        'descripcion',
        'codigo',
        'matriz__nombre',
        'responsable_control'
    ]
    
    readonly_fields = [
        'zona_riesgo_display',
        'valor_riesgo_display'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                ('matriz', 'numero'),
                ('codigo', 'fecha'),
                'nombre',
                'descripcion',
                'tipo_riesgo'
            )
        }),
        ('Evaluación del Riesgo', {
            'fields': (
                ('probabilidad', 'impacto'),
                'zona_riesgo_display',
                'valor_riesgo_display',
                'efectos'
            )
        }),
        ('Controles', {
            'fields': (
                'controles_existentes',
                ('tipo_control', 'efectividad_control'),
                'controles_evaluacion'
            )
        }),
        ('Tratamiento', {
            'fields': (
                'tratamiento',
                'responsable_control',
                'aceptado'
            )
        }),
    )
    
    inlines = [CausaRiesgoInline]
    
    def zona_riesgo_display(self, obj):
        zona = obj.calcular_zona_riesgo()
        color_map = {
            'EXTREMA': '#dc2626',
            'ALTA': '#ea580c',
            'MODERADA': '#ca8a04',
            'BAJA': '#16a34a',
            'MUY BAJA': '#059669'
        }
        color = color_map.get(zona['nivel'], '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">'
            '{}</span>',
            color, zona['nivel']
        )
    zona_riesgo_display.short_description = 'Zona de Riesgo'
    
    def valor_riesgo_display(self, obj):
        zona = obj.calcular_zona_riesgo()
        return f"{zona['valor']} (P:{obj.probabilidad} × I:{obj.impacto})"
    valor_riesgo_display.short_description = 'Valor de Riesgo'
    
    def aceptado_display(self, obj):
        if obj.aceptado:
            return format_html(
                '<span style="color: #16a34a; font-weight: bold;">✓ Sí</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc2626; font-weight: bold;">✗ No</span>'
            )
    aceptado_display.short_description = 'Aceptado'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('matriz')

@admin.register(CausaRiesgo)
class CausaRiesgoAdmin(admin.ModelAdmin):
    list_display = [
        'riesgo',
        'orden',
        'causa_truncada',
        'factor',
        'controles_truncados'
    ]
    
    list_filter = [
        'factor',
        'riesgo__matriz__empresa',
        'riesgo__matriz'
    ]
    
    search_fields = [
        'causa',
        'controles',
        'riesgo__nombre',
        'riesgo__matriz__nombre'
    ]
    
    ordering = ['riesgo', 'orden']
    
    def causa_truncada(self, obj):
        return obj.causa[:100] + '...' if len(obj.causa) > 100 else obj.causa
    causa_truncada.short_description = 'Causa'
    
    def controles_truncados(self, obj):
        if obj.controles:
            return obj.controles[:50] + '...' if len(obj.controles) > 50 else obj.controles
        return 'Sin controles'
    controles_truncados.short_description = 'Controles'

@admin.register(ParametroMatriz)
class ParametroMatrizAdmin(admin.ModelAdmin):
    list_display = [
        'tipo',
        'valor', 
        'etiqueta',
        'descripcion_truncada',
        'activo'
    ]
    
    list_filter = [
        'tipo',
        'activo',
        'valor'
    ]
    
    search_fields = [
        'etiqueta',
        'descripcion'
    ]
    
    ordering = ['tipo', 'valor']
    
    fieldsets = (
        ('Información Principal', {
            'fields': (
                ('tipo', 'valor'),
                'etiqueta',
                'descripcion'
            )
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )
    
    def descripcion_truncada(self, obj):
        return obj.descripcion[:100] + '...' if len(obj.descripcion) > 100 else obj.descripcion
    descripcion_truncada.short_description = 'Descripción'

@admin.register(AuditoriaMatriz)
class AuditoriaMatrizAdmin(admin.ModelAdmin):
    list_display = [
        'fecha_accion',
        'matriz',
        'usuario',
        'accion',
        'descripcion_truncada'
    ]
    
    list_filter = [
        'accion',
        'fecha_accion',
        'matriz__empresa',
        'usuario'
    ]
    
    search_fields = [
        'matriz__nombre',
        'usuario__first_name',
        'usuario__last_name',
        'descripcion'
    ]
    
    readonly_fields = [
        'fecha_accion',
        'datos_anteriores_display',
        'datos_nuevos_display'
    ]
    
    ordering = ['-fecha_accion']
    
    fieldsets = (
        ('Información Principal', {
            'fields': (
                ('matriz', 'usuario'),
                ('accion', 'fecha_accion'),
                'descripcion'
            )
        }),
        ('Datos de Auditoría', {
            'fields': (
                'datos_anteriores_display',
                'datos_nuevos_display'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def descripcion_truncada(self, obj):
        return obj.descripcion[:100] + '...' if len(obj.descripcion) > 100 else obj.descripcion
    descripcion_truncada.short_description = 'Descripción'
    
    def datos_anteriores_display(self, obj):
        if obj.datos_anteriores:
            import json
            return format_html(
                '<pre style="max-height: 200px; overflow-y: scroll; background: #f8f9fa; padding: 10px; border-radius: 4px;">{}</pre>',
                json.dumps(obj.datos_anteriores, indent=2, ensure_ascii=False)
            )
        return 'N/A'
    datos_anteriores_display.short_description = 'Datos Anteriores'
    
    def datos_nuevos_display(self, obj):
        if obj.datos_nuevos:
            import json
            return format_html(
                '<pre style="max-height: 200px; overflow-y: scroll; background: #f8f9fa; padding: 10px; border-radius: 4px;">{}</pre>',
                json.dumps(obj.datos_nuevos, indent=2, ensure_ascii=False)
            )
        return 'N/A'
    datos_nuevos_display.short_description = 'Datos Nuevos'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('matriz', 'usuario')

# ACCIONES PERSONALIZADAS PARA EL ADMIN

@admin.action(description='Recalcular zonas de riesgo seleccionados')
def recalcular_zonas_riesgo(modeladmin, request, queryset):
    """Acción para recalcular las zonas de riesgo"""
    actualizados = 0
    for riesgo in queryset:
        # Forzar recálculo guardando el objeto
        riesgo.save()
        actualizados += 1
    
    modeladmin.message_user(
        request,
        f'Se recalcularon {actualizados} zonas de riesgo exitosamente.',
        level='SUCCESS'
    )

@admin.action(description='Marcar riesgos como aceptados')
def marcar_aceptados(modeladmin, request, queryset):
    """Acción para marcar riesgos como aceptados"""
    updated = queryset.update(aceptado=True)
    modeladmin.message_user(
        request,
        f'Se marcaron {updated} riesgos como aceptados.',
        level='SUCCESS'
    )

@admin.action(description='Marcar riesgos como no aceptados')
def marcar_no_aceptados(modeladmin, request, queryset):
    """Acción para marcar riesgos como no aceptados"""
    updated = queryset.update(aceptado=False)
    modeladmin.message_user(
        request,
        f'Se marcaron {updated} riesgos como no aceptados.',
        level='SUCCESS'
    )

# Agregar las acciones a RiesgoMatrizAdmin
RiesgoMatrizAdmin.actions = [
    recalcular_zonas_riesgo,
    marcar_aceptados,
    marcar_no_aceptados
]

# FILTROS PERSONALIZADOS

class ZonaRiesgoFilter(admin.SimpleListFilter):
    """Filtro para mostrar riesgos por zona de riesgo"""
    title = 'Zona de Riesgo'
    parameter_name = 'zona_riesgo'
    
    def lookups(self, request, model_admin):
        return (
            ('extrema', 'Extrema'),
            ('alta', 'Alta'),
            ('moderada', 'Moderada'),
            ('baja', 'Baja'),
            ('muy_baja', 'Muy Baja'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'extrema':
            return queryset.filter(probabilidad__gte=3, impacto__gte=5)
        elif self.value() == 'alta':
            # Lógica para alta (valor >= 10 pero < 15)
            riesgos_alta = []
            for riesgo in queryset:
                valor = riesgo.probabilidad * riesgo.impacto
                if 10 <= valor < 15:
                    riesgos_alta.append(riesgo.id)
            return queryset.filter(id__in=riesgos_alta)
        elif self.value() == 'moderada':
            # Lógica para moderada (valor >= 6 pero < 10)
            riesgos_moderada = []
            for riesgo in queryset:
                valor = riesgo.probabilidad * riesgo.impacto
                if 6 <= valor < 10:
                    riesgos_moderada.append(riesgo.id)
            return queryset.filter(id__in=riesgos_moderada)
        elif self.value() == 'baja':
            # Lógica para baja (valor >= 3 pero < 6)
            riesgos_baja = []
            for riesgo in queryset:
                valor = riesgo.probabilidad * riesgo.impacto
                if 3 <= valor < 6:
                    riesgos_baja.append(riesgo.id)
            return queryset.filter(id__in=riesgos_baja)
        elif self.value() == 'muy_baja':
            # Lógica para muy baja (valor < 3)
            riesgos_muy_baja = []
            for riesgo in queryset:
                valor = riesgo.probabilidad * riesgo.impacto
                if valor < 3:
                    riesgos_muy_baja.append(riesgo.id)
            return queryset.filter(id__in=riesgos_muy_baja)
        return queryset

class EfectividadControlFilter(admin.SimpleListFilter):
    """Filtro para mostrar riesgos por efectividad de control"""
    title = 'Efectividad de Control'
    parameter_name = 'efectividad_control'
    
    def lookups(self, request, model_admin):
        return (
            ('alta', 'Alta (80-100%)'),
            ('media', 'Media (50-79%)'),
            ('baja', 'Baja (20-49%)'),
            ('muy_baja', 'Muy Baja (0-19%)'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'alta':
            return queryset.filter(efectividad_control__gte=80)
        elif self.value() == 'media':
            return queryset.filter(efectividad_control__gte=50, efectividad_control__lt=80)
        elif self.value() == 'baja':
            return queryset.filter(efectividad_control__gte=20, efectividad_control__lt=50)
        elif self.value() == 'muy_baja':
            return queryset.filter(efectividad_control__lt=20)
        return queryset

# Agregar los filtros personalizados
RiesgoMatrizAdmin.list_filter = RiesgoMatrizAdmin.list_filter + [
    ZonaRiesgoFilter,
    EfectividadControlFilter
]