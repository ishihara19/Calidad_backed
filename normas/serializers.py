from rest_framework import serializers
from .models import Norma, Caracteristica, SubCaracteristica

# ✅ SERIALIZERS BÁSICOS (sin anidación)
class SubCaracteristicaSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple para subcaracterísticas (sin relaciones)"""
    class Meta:
        model = SubCaracteristica
        fields = [
            'id', 'nombre', 'descripcion', 'criterios_evaluacion', 
            'orden', 'es_obligatoria'
        ]

class CaracteristicaSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple para características (sin relaciones)"""
    numero_subcaracteristicas = serializers.ReadOnlyField(source='get_numero_subcaracteristicas')
    
    class Meta:
        model = Caracteristica
        fields = [
            'id', 'nombre', 'descripcion', 'porcentaje_peso', 
            'orden', 'es_obligatoria', 'numero_subcaracteristicas'
        ]

class NormaSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple para normas (sin relaciones)"""
    numero_caracteristicas = serializers.SerializerMethodField()
    
    class Meta:
        model = Norma
        fields = [
            'id', 'nombre', 'descripcion', 'version', 'estado',
            'fecha_creacion', 'fecha_actualizacion', 'numero_caracteristicas'
        ]
    
    def get_numero_caracteristicas(self, obj):
        return obj.caracteristicas.count()

# ✅ SERIALIZERS CON DATOS ANIDADOS (solo para casos específicos)
class SubCaracteristicaDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para subcaracterísticas"""
    caracteristica_nombre = serializers.CharField(source='caracteristica.nombre', read_only=True)
    
    class Meta:
        model = SubCaracteristica
        fields = [
            'id', 'caracteristica', 'caracteristica_nombre', 'nombre', 
            'descripcion', 'criterios_evaluacion', 'orden', 'es_obligatoria'
        ]

class CaracteristicaDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para características CON subcaracterísticas"""
    subcaracteristicas = SubCaracteristicaSimpleSerializer(many=True, read_only=True)
    norma_nombre = serializers.CharField(source='norma.nombre', read_only=True)
    
    class Meta:
        model = Caracteristica
        fields = [
            'id', 'norma', 'norma_nombre', 'nombre', 'descripcion', 
            'porcentaje_peso', 'orden', 'es_obligatoria', 'subcaracteristicas'
        ]

class NormaDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para normas CON características y subcaracterísticas"""
    caracteristicas = CaracteristicaDetailSerializer(many=True, read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.get_full_name', read_only=True)
    porcentajes_validos = serializers.SerializerMethodField()
    
    class Meta:
        model = Norma
        fields = [
            'id', 'nombre', 'descripcion', 'version', 'estado',
            'fecha_creacion', 'fecha_actualizacion', 'creado_por', 'creado_por_nombre',
            'caracteristicas', 'porcentajes_validos'
        ]
    
    def get_porcentajes_validos(self, obj):
        """Verificar que los porcentajes sumen 100%"""
        return obj.validar_porcentajes()

# ✅ SERIALIZERS PARA LISTAS (ultra-optimizados)
class NormaListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listados de normas"""
    numero_caracteristicas = serializers.IntegerField(read_only=True)  # Anotado en queryset
    creado_por_nombre = serializers.CharField(source='creado_por.get_full_name', read_only=True)
    
    class Meta:
        model = Norma
        fields = [
            'id', 'nombre', 'version', 'estado', 'fecha_creacion',
            'numero_caracteristicas', 'creado_por_nombre'
        ]

class CaracteristicaListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listados de características"""
    norma_nombre = serializers.CharField(source='norma.nombre', read_only=True)
    numero_subcaracteristicas = serializers.IntegerField(read_only=True)  # Anotado en queryset
    
    class Meta:
        model = Caracteristica
        fields = [
            'id', 'norma', 'norma_nombre', 'nombre', 'porcentaje_peso',
            'orden', 'numero_subcaracteristicas'
        ]

# ✅ SERIALIZERS PARA CASOS ESPECÍFICOS
class NormaPlantillaSerializer(serializers.ModelSerializer):
    """Serializer específico para generar plantillas de evaluación"""
    caracteristicas_obligatorias = serializers.SerializerMethodField()
    
    class Meta:
        model = Norma
        fields = ['id', 'nombre', 'descripcion', 'version', 'caracteristicas_obligatorias']
    
    def get_caracteristicas_obligatorias(self, obj):
        """Solo características obligatorias con sus subcaracterísticas obligatorias"""
        caracteristicas = obj.caracteristicas.filter(es_obligatoria=True).order_by('orden')
        resultado = []
        
        for car in caracteristicas:
            subcaracteristicas = car.subcaracteristicas.filter(es_obligatoria=True).order_by('orden')
            resultado.append({
                'id': car.id,
                'nombre': car.nombre,
                'descripcion': car.descripcion,
                'porcentaje_peso': car.porcentaje_peso,
                'subcaracteristicas': [
                    {
                        'id': sub.id,
                        'nombre': sub.nombre,
                        'descripcion': sub.descripcion,
                        'criterios_evaluacion': sub.criterios_evaluacion
                    }
                    for sub in subcaracteristicas
                ]
            })
        return resultado

# ✅ SERIALIZER PARA VALIDACIÓN DE PORCENTAJES
class ValidarPorcentajesSerializer(serializers.Serializer):
    """Serializer para validar que los porcentajes de características sumen 100%"""
    norma_id = serializers.IntegerField()
    
    def validate_norma_id(self, value):
        try:
            norma = Norma.objects.get(id=value)
        except Norma.DoesNotExist:
            raise serializers.ValidationError("Norma no encontrada")
        
        if not norma.validar_porcentajes():
            total = sum(car.porcentaje_peso for car in norma.caracteristicas.all())
            raise serializers.ValidationError(
                f"Los porcentajes no suman 100%. Total actual: {total}%"
            )
        
        return value