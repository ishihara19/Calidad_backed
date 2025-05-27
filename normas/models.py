from django.db import models
from django.conf import settings
from empresa.models import Empresa
from django.core.validators import MaxValueValidator,MinValueValidator
from decimal import Decimal

# Create your models here.
class Norma(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    version = models.CharField(max_length=10)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True,
        related_name='normas_creadas'
    )
    estado = models.CharField(
        max_length=20,
        choices=[
            ('borrador', 'Borrador'),
            ('revision', 'En Revisión'),
            ('aprobada', 'Aprobada'),
            ('obsoleta', 'Obsoleta')
        ],
        default='borrador'
    )

    class Meta:
        verbose_name = "Norma"
        verbose_name_plural = "Normas"
        permissions = [
            ("can_approve_norma", "Puede aprobar normas"),
            ("can_review_norma", "Puede revisar normas"),
            ("can_create_norma", "Puede crear normas"),
        ]

    def __str__(self):
        return self.nombre
    
    def validar_porcentajes(self):
        """Valida que los porcentajes de características sumen 100%"""
        total = sum(car.porcentaje_peso for car in self.caracteristicas.all())
        return abs(total - Decimal('100.00')) < Decimal('0.01')  # Tolerancia de 0.01%

class Caracteristica(models.Model):
    norma = models.ForeignKey(Norma, on_delete=models.CASCADE, related_name='caracteristicas')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    
    # NUEVO: Porcentaje de peso en la evaluación total
    porcentaje_peso = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=Decimal('0.00'),
        verbose_name="Porcentaje de peso (%)",
        help_text="Peso de esta característica en la evaluación total. Todas deben sumar 100%"
    )
    
    # Orden para mostrar en evaluaciones
    orden = models.PositiveIntegerField(
        default=1,
        verbose_name="Orden de presentación"
    )
    
    # Indica si es obligatoria en evaluaciones
    es_obligatoria = models.BooleanField(
        default=True,
        verbose_name="¿Es obligatoria en evaluaciones?"
    )

    class Meta:
        verbose_name = "Característica"
        verbose_name_plural = "Características"
        ordering = ['orden', 'nombre']
        unique_together = ['norma', 'nombre']  # No duplicar nombres en la misma norma

    def __str__(self):
        return f"{self.norma.nombre} - {self.nombre} ({self.porcentaje_peso}%)"
    
    def get_numero_subcaracteristicas(self):
        """Retorna el número de subcaracterísticas"""
        return self.subcaracteristicas.count()
    
    def get_puntuacion_maxima_posible(self):
        """Calcula la puntuación máxima posible (número de subs * 3)"""
        return self.subcaracteristicas.count() * 3

class SubCaracteristica(models.Model):
    caracteristica = models.ForeignKey(Caracteristica, on_delete=models.CASCADE, related_name='subcaracteristicas')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    
    # Información adicional para evaluadores
    criterios_evaluacion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Criterios de evaluación",
        help_text="Guía específica para evaluar esta subcaracterística"
    )
    
    orden = models.PositiveIntegerField(
        default=1,
        verbose_name="Orden de presentación"
    )
    
    es_obligatoria = models.BooleanField(
        default=True,
        verbose_name="¿Es obligatoria en evaluaciones?"
    )

    class Meta:
        verbose_name = "Subcaracterística"
        verbose_name_plural = "Subcaracterísticas"
        ordering = ['orden', 'nombre']
        unique_together = ['caracteristica', 'nombre']

    def __str__(self):
        return f"{self.caracteristica.nombre} - {self.nombre}"

