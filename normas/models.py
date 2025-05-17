from django.db import models
from django.conf import settings
from empresa.models import Empresa
# Create your models here.
class Norma(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()

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
    
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL,null=True, on_delete=models.CASCADE, related_name='preguntas_usuario')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE,null=True, related_name="preguntas_empresa")
    subcaracteristica = models.ForeignKey(SubCaracteristica, on_delete=models.CASCADE, related_name='preguntas')
    observacion = models.TextField(blank=True, null=True)
    puntos = models.IntegerField()
    valor_maximo = models.IntegerField(default=3)

    def __str__(self):
        return f"{self.subcaracteristica.nombre}: {self.usuario} - {self.empresa}"