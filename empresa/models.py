from django.db import models
from API_C.utils import generate_unique_id, generar_codigo_empresa
# Create your models here.
class Empresa(models.Model):
    
    id = models.CharField(max_length=14,primary_key=True, editable=False)
    nombre = models.CharField(max_length=100)
    nit = models.CharField(max_length=20, unique=True, blank=False, null=False)
    direccion = models.CharField(max_length=255)
    email = models.EmailField()
    telefono = models.CharField(max_length=15)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    codigo_empresa = models.CharField(max_length=8,null=True,blank=True)
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
    
    def __str__(self):
        return f"{self.id} - {self.nombre}"
    
    def save(self,*args, **kwargs):
        
        if not self.codigo_empresa:
            self.codigo_empresa = generar_codigo_empresa(Empresa)
            
        if not self.id:
            prefix = f"Em-{self.nit}"
            self.id = generate_unique_id(Empresa,prefix)  
        super().save(*args, **kwargs)        