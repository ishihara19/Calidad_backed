from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from decimal import Decimal
from normas.models import Norma, Caracteristica, SubCaracteristica
from software.models import Software
from API_C.utils import generar_codigo_evaluacion

class Evaluacion(models.Model):
    """
    Evaluación principal de un software específico basada en una norma ISO 25000
    """
    class EstadoEvaluacion(models.TextChoices):
        BORRADOR = 'borrador', 'Borrador'
        EN_PROGRESO = 'en_progreso', 'En Progreso'
        COMPLETADA = 'completada', 'Completada'
        APROBADA = 'aprobada', 'Aprobada'
        RECHAZADA = 'rechazada', 'Rechazada'
    
    codigo_evaluacion = models.CharField(
        max_length=15, 
        unique=True, 
        editable=False,
        verbose_name="Código único de evaluación"
    )
    software = models.ForeignKey(
        Software, 
        on_delete=models.CASCADE, 
        related_name='evaluaciones',
        verbose_name="Software evaluado"
    )
    norma = models.ForeignKey(
        Norma, 
        on_delete=models.CASCADE, 
        related_name='evaluaciones',
        verbose_name="Norma aplicada"
    )
    evaluador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='evaluaciones_realizadas',
        verbose_name="Usuario evaluador"
    )
    empresa = models.ForeignKey(
        'empresa.Empresa',
        on_delete=models.CASCADE,
        related_name='evaluaciones',
        verbose_name="Empresa"
    )
    
    # Metadatos de la evaluación
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_completada = models.DateTimeField(null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    estado = models.CharField(
        max_length=20, 
        choices=EstadoEvaluacion.choices, 
        default=EstadoEvaluacion.BORRADOR
    )
    
    # Resultados generales
    puntuacion_total = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Puntuación total (%)"
    )
    observaciones_generales = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Observaciones generales de la evaluación"
    )
    
    class Meta:
        verbose_name = "Evaluación"
        verbose_name_plural = "Evaluaciones"
        unique_together = ['software', 'norma', 'evaluador']  # Una evaluación por software/norma/evaluador
        
    def save(self, *args, **kwargs):
        if not self.codigo_evaluacion:
            # Generar código usando empresa y evaluador
            self.codigo_evaluacion = generar_codigo_evaluacion(
                Evaluacion,
                self.empresa.codigo_empresa if self.empresa.codigo_empresa else 'SIN',
                self.evaluador.document
            )
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.codigo_evaluacion} - {self.software.nombre} ({self.norma.nombre})"
    
    def calcular_puntuacion_total(self):
        """Calcula la puntuación total basada en las calificaciones por característica"""
        calificaciones = self.calificaciones_caracteristica.all()
        if not calificaciones.exists():
            return Decimal('0.00')
        
        total_ponderado = sum(
            (cal.puntuacion_obtenida * cal.caracteristica.porcentaje_peso) / 100
            for cal in calificaciones
        )
        return round(Decimal(str(total_ponderado)), 2)

class CalificacionCaracteristica(models.Model):
    """
    Calificación de una característica específica dentro de una evaluación
    """
    evaluacion = models.ForeignKey(
        Evaluacion,
        on_delete=models.CASCADE,
        related_name='calificaciones_caracteristica'
    )
    caracteristica = models.ForeignKey(
        Caracteristica,
        on_delete=models.CASCADE,
        related_name='calificaciones'
    )
    
    # Resultados de la característica
    puntuacion_obtenida = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Puntuación obtenida (%)"
    )
    puntuacion_maxima = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('100.00'),
        verbose_name="Puntuación máxima (%)"
    )
    
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones de la característica"
    )
    fecha_calificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Calificación de Característica"
        verbose_name_plural = "Calificaciones de Características"
        unique_together = ['evaluacion', 'caracteristica']
        
    def __str__(self):
        return f"{self.evaluacion.codigo_evaluacion} - {self.caracteristica.nombre}: {self.puntuacion_obtenida}%"
    
    def calcular_puntuacion_caracteristica(self):
        """
        Calcula la puntuación de la característica basada en sus subcaracterísticas
        """
        calificaciones_sub = self.calificaciones_subcaracteristica.all()
        if not calificaciones_sub.exists():
            return Decimal('0.00')
        
        # Promedio de subcaracterísticas convertido a porcentaje
        total_puntos = sum(cal.puntos for cal in calificaciones_sub)
        max_puntos = calificaciones_sub.count() * 3  # 3 es el máximo por subcaracterística
        
        if max_puntos == 0:
            return Decimal('0.00')
            
        porcentaje = (total_puntos / max_puntos) * 100
        return round(Decimal(str(porcentaje)), 2)

class CalificacionSubCaracteristica(models.Model):
    """
    Calificación individual de subcaracterísticas (migrado desde normas/)
    """
    calificacion_caracteristica = models.ForeignKey(
        CalificacionCaracteristica,
        on_delete=models.CASCADE,
        related_name='calificaciones_subcaracteristica'
    )
    subcaracteristica = models.ForeignKey(
        SubCaracteristica,
        on_delete=models.CASCADE,
        related_name='calificaciones'
    )
    
    # Calificación (0-3 puntos)
    puntos = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(3)],
        verbose_name="Puntos obtenidos (0-3)"
    )
    puntos_maximo = models.IntegerField(
        default=3,
        verbose_name="Puntos máximos"
    )
    
    observacion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observación/Justificación"
    )
    evidencia_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="URL de evidencia (opcional)"
    )
    fecha_calificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Calificación de Subcaracterística"
        verbose_name_plural = "Calificaciones de Subcaracterísticas"
        unique_together = ['calificacion_caracteristica', 'subcaracteristica']
    
    def __str__(self):
        return f"{self.subcaracteristica.nombre}: {self.puntos}/3"
    
    @property
    def porcentaje_obtenido(self):
        if self.puntos is None or self.puntos_maximo in (None, 0):
            return 0
        return round((self.puntos / self.puntos_maximo) * 100, 2)