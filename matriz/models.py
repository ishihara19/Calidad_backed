# matriz/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from API_C.utils import generate_unique_id
import json

class MatrizRiesgo(models.Model):
    """Modelo principal para las matrices de riesgo"""
    
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Matriz")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    responsable = models.CharField(max_length=100, blank=True, verbose_name="Responsable")
    fecha_creacion = models.DateField(verbose_name="Fecha de Creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Modificación")
    
    # Relación con usuario y empresa
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Creado por"
    )
    empresa = models.ForeignKey(
        'empresa.Empresa',
        on_delete=models.CASCADE,
        related_name='matrices_riesgo',
        verbose_name="Empresa"
    )
    
    class Meta:
        verbose_name = "Matriz de Riesgo"
        verbose_name_plural = "Matrices de Riesgo"
        ordering = ['-fecha_modificacion']
    
    def __str__(self):
        return self.nombre
    
    def save(self, *args, **kwargs):
        if not self.id:
            prefix = f"MR-{self.empresa.codigo_empresa if self.empresa.codigo_empresa else 'SIN'}"
            self.id = generate_unique_id(MatrizRiesgo, prefix)
        super().save(*args, **kwargs)
    
    @property
    def total_riesgos(self):
        return self.riesgos.count()
    
    @property
    def resumen_riesgos_por_nivel(self):
        resumen = {'EXTREMA': 0, 'ALTA': 0, 'MODERADA': 0, 'BAJA': 0, 'MUY_BAJA': 0}
        for riesgo in self.riesgos.all():
            zona = riesgo.calcular_zona_riesgo()
            nivel_key = zona['nivel'].replace(' ', '_')
            if nivel_key in resumen:
                resumen[nivel_key] += 1
        return resumen


class RiesgoMatriz(models.Model):
    """Modelo para los riesgos individuales dentro de una matriz"""
    
    TIPOS_RIESGO = [
        ('Operativo', 'Operativo'),
        ('Estratégico', 'Estratégico'),
        ('Financiero', 'Financiero'),
        ('Cumplimiento', 'Cumplimiento'),
        ('Tecnológico', 'Tecnológico'),
    ]
    
    TIPOS_CONTROL = [
        ('Preventivo', 'Preventivo'),
        ('Correctivo', 'Correctivo'),
        ('Detectivo', 'Detectivo'),
    ]
    
    # Relación con la matriz
    matriz = models.ForeignKey(
        MatrizRiesgo, 
        on_delete=models.CASCADE, 
        related_name='riesgos'
    )
    
    # Información básica del riesgo
    numero = models.PositiveIntegerField(verbose_name="Número")
    fecha = models.DateField(verbose_name="Fecha")
    codigo = models.CharField(max_length=50, blank=True, verbose_name="Código")
    nombre = models.CharField(max_length=300, verbose_name="Nombre del Riesgo")
    descripcion = models.TextField(blank=True, verbose_name="Descripción del Riesgo")
    efectos = models.TextField(blank=True, verbose_name="Efectos/Consecuencias")
    tipo_riesgo = models.CharField(
        max_length=20, 
        choices=TIPOS_RIESGO, 
        blank=True, 
        verbose_name="Tipo de Riesgo"
    )
    
    # Evaluación del riesgo
    probabilidad = models.IntegerField(
        default=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)], 
        verbose_name="Probabilidad"
    )
    impacto = models.IntegerField(
        default=1, 
        validators=[MinValueValidator(1), MaxValueValidator(5)], 
        verbose_name="Impacto"
    )
    
    # Controles
    controles_existentes = models.TextField(
        blank=True, 
        verbose_name="Controles Existentes"
    )
    tipo_control = models.CharField(
        max_length=20, 
        choices=TIPOS_CONTROL, 
        default='Preventivo', 
        verbose_name="Tipo de Control"
    )
    efectividad_control = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(100)], 
        verbose_name="Efectividad del Control (%)"
    )
    
    # Evaluación de controles (almacenado como JSON)
    controles_evaluacion = models.JSONField(
        default=dict, 
        blank=True, 
        verbose_name="Evaluación de Controles"
    )
    
    # Tratamiento
    tratamiento = models.TextField(
        blank=True, 
        verbose_name="Tratamiento/Controles Propuestos"
    )
    responsable_control = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Responsable del Control"
    )
    aceptado = models.BooleanField(
        default=False, 
        verbose_name="¿Se acepta el riesgo?"
    )
    
    class Meta:
        verbose_name = "Riesgo"
        verbose_name_plural = "Riesgos"
        ordering = ['numero']
        unique_together = ['matriz', 'numero']
    
    def __str__(self):
        return f"{self.codigo or self.numero} - {self.nombre}"
    
    def calcular_zona_riesgo(self):
        """Calcula la zona de riesgo basada en probabilidad e impacto"""
        valor = self.probabilidad * self.impacto
        if valor >= 15:
            return {'nivel': 'EXTREMA', 'color': 'bg-red-600', 'valor': valor}
        elif valor >= 10:
            return {'nivel': 'ALTA', 'color': 'bg-red-400', 'valor': valor}
        elif valor >= 6:
            return {'nivel': 'MODERADA', 'color': 'bg-yellow-400', 'valor': valor}
        elif valor >= 3:
            return {'nivel': 'BAJA', 'color': 'bg-green-400', 'valor': valor}
        else:
            return {'nivel': 'MUY BAJA', 'color': 'bg-green-600', 'valor': valor}
    
    @property
    def zona_riesgo(self):
        return self.calcular_zona_riesgo()
    
    def save(self, *args, **kwargs):
        # Inicializar controles_evaluacion si está vacío
        if not self.controles_evaluacion:
            self.controles_evaluacion = {
                'herramienta': False,
                'manuales': False,
                'efectividad': False,
                'responsables': False,
                'frecuencia': False
            }
        super().save(*args, **kwargs)


class CausaRiesgo(models.Model):
    """Modelo para las causas de un riesgo"""
    
    FACTORES_CAUSA = [
        ('Información', 'Información'),
        ('Método', 'Método'),
        ('Personas', 'Personas'),
        ('Sistemas de información', 'Sistemas de información'),
        ('Infraestructura', 'Infraestructura'),
    ]
    
    riesgo = models.ForeignKey(
        RiesgoMatriz, 
        on_delete=models.CASCADE, 
        related_name='causas'
    )
    causa = models.TextField(verbose_name="Descripción de la Causa")
    factor = models.CharField(
        max_length=50, 
        choices=FACTORES_CAUSA, 
        blank=True, 
        verbose_name="Factor de Causa"
    )
    controles = models.TextField(
        blank=True, 
        verbose_name="Controles Asociados"
    )
    orden = models.PositiveIntegerField(default=1, verbose_name="Orden")
    
    class Meta:
        verbose_name = "Causa del Riesgo"
        verbose_name_plural = "Causas del Riesgo"
        ordering = ['orden']
    
    def __str__(self):
        return f"Causa {self.orden}: {self.causa[:50]}..."


class ParametroMatriz(models.Model):
    """Modelo para los parámetros configurables del sistema"""
    
    TIPOS_PARAMETRO = [
        ('PROBABILIDAD', 'Probabilidad'),
        ('IMPACTO', 'Impacto'),
    ]
    
    tipo = models.CharField(
        max_length=20, 
        choices=TIPOS_PARAMETRO, 
        verbose_name="Tipo de Parámetro"
    )
    valor = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], 
        verbose_name="Valor"
    )
    etiqueta = models.CharField(max_length=50, verbose_name="Etiqueta")
    descripcion = models.TextField(verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        verbose_name = "Parámetro del Sistema"
        verbose_name_plural = "Parámetros del Sistema"
        unique_together = ['tipo', 'valor']
        ordering = ['tipo', 'valor']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.valor}: {self.etiqueta}"


class AuditoriaMatriz(models.Model):
    """Modelo para auditar cambios en las matrices"""
    
    ACCIONES = [
        ('CREATE', 'Creación'),
        ('UPDATE', 'Actualización'),
        ('DELETE', 'Eliminación'),
    ]
    
    matriz = models.ForeignKey(
        MatrizRiesgo, 
        on_delete=models.CASCADE, 
        related_name='auditoria'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    accion = models.CharField(max_length=10, choices=ACCIONES)
    descripcion = models.TextField(
        blank=True, 
        verbose_name="Descripción del cambio"
    )
    fecha_accion = models.DateTimeField(auto_now_add=True)
    datos_anteriores = models.JSONField(
        null=True, 
        blank=True, 
        verbose_name="Datos anteriores"
    )
    datos_nuevos = models.JSONField(
        null=True, 
        blank=True, 
        verbose_name="Datos nuevos"
    )
    
    class Meta:
        verbose_name = "Auditoría de Matriz"
        verbose_name_plural = "Auditorías de Matrices"
        ordering = ['-fecha_accion']
    
    def __str__(self):
        return f"{self.matriz.nombre} - {self.get_accion_display()} - {self.fecha_accion.strftime('%d/%m/%Y %H:%M')}"