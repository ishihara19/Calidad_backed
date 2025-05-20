from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator,MinValueValidator


class Riesgos(models.Model):   
    nombre = models.CharField(max_length=30, verbose_name="Nombre del riesgo")
    def __str__(self):
        return self.nombre
    
class Procesos(models.Model):
    nombre = models.CharField(max_length=30, verbose_name="Nombre del proceso")
    descripcion = models.CharField(max_length=255, verbose_name="Descipcion del proceso")
    def __str__(self):
        return self.nombre
    
class TipoRiesgos(models.Model):   
    nombre = models.CharField(max_length=50, verbose_name="Nombre del tipo de riesgo")
    def __str__(self):
        return self.nombre
    
class RiesgoAsociados(models.Model):
    nombre = models.CharField(max_length=30, verbose_name="Nombre de los riesgos asociados")
    def __str__(self):
        return self.nombre    

class PosibleOcurrencia(models.Model):
    nombre = models.CharField(max_length=50, verbose_name="Nombee de posibles ocurrencia")
    valor = models.IntegerField(validators=[MinValueValidator(1),MaxValueValidator(5)], help_text="Valor de posible ocurrencia Debe de ser entre 0 y 5")
    def __str__(self):
        return self.nombre
# 
class Impacto(models.Model):
    nombre = models.CharField(max_length=50, verbose_name="Nombre de impactos")
    valor = models.IntegerField(validators=[MinValueValidator(1),MaxValueValidator(5)], help_text="Valor de impacto Debe de ser entre 0 y 5")
    def __str__(self):
        return self.nombre
    
class OpcionTratamiento(models.Model):
    nombre = models.CharField(max_length=50, verbose_name="Nombre de opcion de tratamiento de riego")
    def __str__(self):
        return self.nombre        
    
class Matriz(models.Model):
    
    class RiesgoAfectacion(models.TextChoices):
        SI = "SI", ("SI")
        NO = "NO", ("NO")
        NA = "NA", ("NA")
        
    class TipoImpacto(models.TextChoices):
        CONTINUIDAD_OPERATIVA = "Continuidad Operativa",("Continuidad Operativa")
        IMAGEN = "Imagen",("Imagen")
        LEGAL = "Legal", ("Legal")
    
    class ZonaRiesgo(models.TextChoices):
        BAJA = "BAJA",("BAJA")
        MODERADA = "MODERADA",("MODERADA")
        ALTA = "ALTA", ("ALTA")
        EXTREMA = "EXTREMA",("EXTREMA")
    
    class TipoControl(models.TextChoices):
        PREVENTIVO = "Preventivo", ("Preventivo")
        CORRECTIVO = "Correctivo", ("Correctivo")
        N_A = "N/A",("N/A")    
                        
        
    id = models.CharField(max_length=10, primary_key=True, verbose_name="Id matriz", help_text="ID de la matriz de riesgo", db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Usuario", help_text="Usuario que realiza la accion al crear una matriz de risgo")
    fecha_riesgo = models.DateField(verbose_name="Fecha identificacion riesgo",help_text="Fecha de identificación riesgo")
    codigo_riesgo = models.CharField(verbose_name="Codigo del riesgo",help_text="Código del riesgo")
    riesgo = models.ForeignKey(Riesgos, on_delete=models.CASCADE, verbose_name="Tipo de riesgo",help_text="Riesgo")
    descripcion = models.CharField(max_length=255, verbose_name="Definición y Descripción del riesgo", help_text="Definición y Descripción del riesgo")
    causas = models.TextField(verbose_name="Causas de riesgo", help_text="Causas (un riesgo puede tener mas de una causa) Vulnerabilidad - Amenazas")
    efectos = models.CharField(max_length=255,verbose_name="Definición de los efectos del riesgo", help_text="Definición de los efectos de materialización del riesgo identificado")
    afectacion = models.CharField(max_length=255,verbose_name="Afecta infraestructua crítica", help_text="Riesgo afecta infraestructua crítica" )
    riesgo_afectacion = models.CharField(max_length=2, choices=RiesgoAfectacion,verbose_name="Riesgo afecta",help_text="Riesgo afecta infraestructua crítica")
    informacion_asosiada = models.CharField(max_length=255, verbose_name="Activos de informacion", help_text="Activos de Información Asociados" )
    tipo_activo = models.CharField(max_length=255, verbose_name="Tipo de activo",help_text="Tipo de activo vinculado")
    criterio_activo = models.CharField(max_length=255, verbose_name="Criticidad del activo", help_text="Criticidad del activo")
    proceso = models.ForeignKey(Procesos, on_delete=models.CASCADE, verbose_name="Proceso", help_text="Proceso")
    dueño_riesgo = models.CharField(max_length=100, verbose_name="Dueño del riesgo", help_text="Dueño o propietario del riesgo")
    rol_dueño_riesgo = models.CharField(max_length=30, verbose_name="Rol dueño del riesgo", help_text="Rol del dueño o propietario del riesgo")
    riesgo_asociados = models.ManyToManyField(RiesgoAsociados)
    tipo_impacto = models.CharField(max_length=50, choices=TipoImpacto, verbose_name="Tipo de Impacto",help_text="Tipo de Impacto")
    controles = models.CharField(max_length=255, verbose_name="Controles existentes",help_text="Controles existentes")    
    Posibilidad_ocurrencia = models.ForeignKey(PosibleOcurrencia, on_delete=models.CASCADE, verbose_name="Posibilidad de Ocurrencia", help_text="Posibilidad de Ocurrencia")
    impacto = models.ForeignKey(Impacto, on_delete=models.CASCADE, verbose_name="Impacto",help_text="Impacto")
    zona_riego = models.CharField(max_length=20, choices=ZonaRiesgo, verbose_name="Zona de riesgo", help_text="Zona de riesgo")
    aceptado = models.CharField(max_length=2, choices=RiesgoAfectacion, verbose_name="¿SE ACEPTA?", help_text="Se acepta o no")
    tratamiento = models.CharField(max_length=255, verbose_name="Tratamiento Controles a implementar", help_text="Tratamiento Controles a implementar")
    opcion_tratamiento = models.ForeignKey(OpcionTratamiento, on_delete=models.CASCADE, verbose_name="Nombe de opcion de tratamiento de riego", help_text="Nombe de opcion de tratamiento de riego")
    tipo_control = models.CharField(max_length=50, verbose_name="Tipo de control", help_text="Tipo de control")
        

