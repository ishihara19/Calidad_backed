from django.db import models
from django.conf import settings
from empresa.models import Empresa
from django.core.validators import MaxValueValidator,MinValueValidator
from API_C.utils import generar_codigo_evaluacion
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

class Caracteristica(models.Model):
    norma = models.ForeignKey(Norma, on_delete=models.CASCADE, related_name='caracteristicas')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()

    def __str__(self):
        return f"{self.norma.nombre}-{self.nombre}"

class SubCaracteristica(models.Model):
    caracteristica = models.ForeignKey(Caracteristica, on_delete=models.CASCADE, related_name='subcaracteristicas')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()

    def __str__(self):
        return f"{self.caracteristica.nombre}-{self.nombre}"

class CalificacionSubCaracteristica(models.Model):
    
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL,null=False, on_delete=models.CASCADE, related_name='preguntas_usuario')
    codigo_calificacion =models.CharField(max_length=10,verbose_name="Codigo unico para evaluacion", null=False, help_text="condigo unico para evaluacion",db_default="")
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="preguntas_empresa")
    subcaracteristica = models.ForeignKey(SubCaracteristica, on_delete=models.CASCADE, related_name='preguntas')
    observacion = models.TextField(blank=True, null=True)
    puntos = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(3)])
    fecha_cracion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creaion",help_text="Fecha de creacion")

    def save(self, *args, **kwargs):
        if not self.codigo_calificacion and self.empresa and self.usuario:
            
            if hasattr(self.usuario, 'document') and self.empresa.codigo_empresa:
                 # La función original que tenías.
                 # Si esta función está diseñada para generar un código *nuevo* siempre, entonces el enfoque de la vista es mejor.
                self.codigo_calificacion = generar_codigo_evaluacion(
                    CalificacionSubCaracteristica, 
                    self.empresa.codigo_empresa, 
                    self.usuario.document
                )
            # else:
                # Manejar caso donde falten datos para generar el código si es un save individual
        super().save(*args, **kwargs)
            
          
    def __str__(self):
        return f"{self.subcaracteristica.nombre}: {self.usuario} - {self.empresa}"