from django.db import models
from empresa.models import Empresa

# Create your models here.
class Software(models.Model):
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE,verbose_name="Emopresa del Software", related_name='Empresa_software')
    nombre = models.CharField(max_length=100, verbose_name="Nombre del software")
    vesion = models.CharField(max_length=50, verbose_name="Versión de software")
    objectivo_general = models.CharField(max_length=500, verbose_name="Objetivos generales del software")
    objetivo_especifico = models.CharField(max_length=500, verbose_name="Objetivos especificos del software")
    fecha_registro = models.DateTimeField(auto_now_add=True, null=True, verbose_name="Fecha de registro del software")
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True, verbose_name="Fecha de actualizacioon")
    codigo_software = models.CharField(max_length=10, null=True, blank=True, verbose_name="Codigo del unico de software")
    url = models.URLField(max_length=500, null=True, blank=True, verbose_name="URL del software")
    
    class Meta:
        verbose_name = 'Software'
        verbose_name_plural = 'Softwares'
    
    def __str__(self):
        return f"{self.codigo_software} - {self.nombre} ({self.vesion})"
    
        
    