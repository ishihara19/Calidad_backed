from django.db import models
from django.conf import settings 
from django.core.validators import MinValueValidator, MaxValueValidator

class Caracteristica(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    codigo = models.CharField(max_length=20, unique=True)
    
    def __str__(self):
        return self.nombre

class Subcaracteristica(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    codigo = models.CharField(max_length=20, unique=True)
    caracteristica = models.ForeignKey(Caracteristica, related_name='subcaracteristicas', on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.caracteristica.codigo}.{self.codigo} - {self.nombre}"

class Pregunta(models.Model):
    texto = models.TextField()
    codigo = models.CharField(max_length=20, unique=True)
    subcaracteristica = models.ForeignKey(Subcaracteristica, related_name='preguntas', on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.codigo} - {self.texto[:50]}"

class Proyecto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    propietario = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='proyectos', on_delete=models.CASCADE)
    
    def __str__(self):
        return self.nombre

class Evaluacion(models.Model):
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('en_progreso', 'En Progreso'),
        ('completada', 'Completada'),
    )
    
    proyecto = models.ForeignKey(Proyecto, related_name='evaluaciones', on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    evaluador = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='evaluaciones', on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    def __str__(self):
        return f"Evaluación de {self.proyecto.nombre} - {self.fecha_creacion.strftime('%Y-%m-%d')}"
    
    def calcular_porcentaje_total(self):
        """Calcula el porcentaje total de cumplimiento"""
        respuestas = self.respuestas.all()
        if not respuestas:
            return 0
        
        suma_valores = sum(r.valor for r in respuestas)
        total_posible = respuestas.count() * 3  # Cada pregunta tiene 3 puntos máximo
        
        if total_posible == 0:
            return 0
        
        return (suma_valores * 100) / total_posible
    
    def obtener_nivel_cumplimiento(self):
        """Determina el nivel de cumplimiento según el porcentaje"""
        porcentaje = self.calcular_porcentaje_total()
        
        if porcentaje <= 30:
            return 0  # No cumple
        elif porcentaje <= 50:
            return 1  # Cumple parcialmente
        elif porcentaje <= 89:
            return 2  # Cumple mayormente
        else:
            return 3  # Cumple totalmente

class RespuestaPregunta(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, related_name='respuestas', on_delete=models.CASCADE)
    pregunta = models.ForeignKey(Pregunta, related_name='respuestas', on_delete=models.CASCADE)
    valor = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(3)])
    observacion = models.TextField(blank=True, null=True)
    evidencia = models.FileField(upload_to='evidencias/', blank=True, null=True)
    
    class Meta:
        unique_together = ('evaluacion', 'pregunta')
    
    def __str__(self):
        return f"{self.pregunta.codigo} - Valor: {self.valor}"