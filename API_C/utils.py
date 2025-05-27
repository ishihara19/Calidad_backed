import hashlib
import uuid
from django.utils import timezone

def generate_unique_id(model,prefix):
        """Genera un ID único para el modelo dado, asegurando que no exista en la base de datos"""
        while True:
            unique_value = str(uuid.uuid4())
            hash_obj = hashlib.md5(unique_value.encode())
            hash_int = int(hash_obj.hexdigest(), 16)
            numeric_part = str(hash_int)[:6] # toma los primeros 6 digitos del hash
            generated_id = prefix + numeric_part# Genera el ID único con el prefijo
            #Verifica si el ID Ya existe en la base de datos            
            if not model.objects.filter(id=generated_id).exists():
                # Si no existe, devuelve el ID generado
                return generated_id
def generar_codigo_empresa(model):
    
    unique_value = str(uuid.uuid4())
    hash_obj = hashlib.md5(unique_value.encode())
    hash = hash_obj.hexdigest()    
    empresa_code = str(hash)[12:-12]
    if not model.objects.filter(codigo_empresa=empresa_code).exists():
        # Si no existe, devuelve el ID generado
        return empresa_code


def generar_codigo_evaluacion(model, codigo_empresa, documento_evaluador):
    """
    Genera un ID único para el modelo dado, asegurando que no exista en la base de datos.
    Agrega un contador incremental si el código base ya existe.
    """
    contador = 0
    while True:
        documento_part = str(documento_evaluador)[-4:]

        # Construye el código base
        codigo_base = f"{codigo_empresa}-{documento_part}"

        # Si el contador es 0, usa el código base. Si no, añade el contador.
        if contador == 0:
            codigo_evaluacion = codigo_base
        else:
            codigo_evaluacion = f"{codigo_base}-{contador}"

        # Verifica si el código_calificacion ya existe en la base de datos
        if not model.objects.filter(codigo_evaluacion=codigo_evaluacion).exists():
            # Si no existe, devuelve el ID generado
            return codigo_evaluacion
        else:
            # Si existe, incrementa el contador y el bucle continuará
            contador += 1           