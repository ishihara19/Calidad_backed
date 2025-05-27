# evaluaciones/serializers.py - VERSIÓN ACTUALIZADA
from rest_framework import serializers
from decimal import Decimal
from .models import Evaluacion, CalificacionCaracteristica, CalificacionSubCaracteristica
from normas.models import Norma, Caracteristica, SubCaracteristica
from software.models import Software

class CalificacionSubCaracteristicaSerializer(serializers.ModelSerializer):
    subcaracteristica_nombre = serializers.CharField(source='subcaracteristica.nombre', read_only=True)
    porcentaje_obtenido = serializers.ReadOnlyField()
    
    class Meta:
        model = CalificacionSubCaracteristica
        fields = [
            'id',
            'subcaracteristica',
            'subcaracteristica_nombre', 
            'puntos',
            'puntos_maximo',
            'observacion',
            'evidencia_url',
            'porcentaje_obtenido',
            'fecha_calificacion'
        ]
        read_only_fields = ['id', 'fecha_calificacion', 'puntos_maximo']
    
    def validate_puntos(self, value):
        if value < 0 or value > 3:
            raise serializers.ValidationError("Los puntos deben estar entre 0 y 3.")
        return value

class CalificacionCaracteristicaSerializer(serializers.ModelSerializer):
    caracteristica_nombre = serializers.CharField(source='caracteristica.nombre', read_only=True)
    calificaciones_subcaracteristica = CalificacionSubCaracteristicaSerializer(many=True, read_only=True)
    numero_subcaracteristicas_evaluadas = serializers.SerializerMethodField()
    puntos_maximos_posibles = serializers.SerializerMethodField()
    
    class Meta:
        model = CalificacionCaracteristica
        fields = [
            'id',
            'caracteristica',
            'caracteristica_nombre',
            'porcentaje_asignado',  # NUEVO CAMPO
            'puntuacion_obtenida',
            'puntuacion_maxima',
            'observaciones',
            'fecha_calificacion',
            'numero_subcaracteristicas_evaluadas',
            'puntos_maximos_posibles',
            'calificaciones_subcaracteristica'
        ]
        read_only_fields = ['id', 'fecha_calificacion', 'puntuacion_maxima']
    
    def get_numero_subcaracteristicas_evaluadas(self, obj):
        return obj.calificaciones_subcaracteristica.count()
    
    def get_puntos_maximos_posibles(self, obj):
        return obj.calificaciones_subcaracteristica.count() * 3
    
    def validate_porcentaje_asignado(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("El porcentaje debe estar entre 0 y 100%.")
        return value
    
    def validate_puntuacion_obtenida(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("La puntuación debe estar entre 0 y 100%.")
        return value

class EvaluacionSerializer(serializers.ModelSerializer):
    software_nombre = serializers.CharField(source='software.nombre', read_only=True)
    norma_nombre = serializers.CharField(source='norma.nombre', read_only=True)
    evaluador_nombre = serializers.CharField(source='evaluador.get_full_name', read_only=True)
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    calificaciones_caracteristica = CalificacionCaracteristicaSerializer(many=True, read_only=True)
    suma_porcentajes = serializers.SerializerMethodField()
    
    class Meta:
        model = Evaluacion
        fields = [
            'id',
            'codigo_evaluacion',
            'software',
            'software_nombre',
            'norma', 
            'norma_nombre',
            'evaluador',
            'evaluador_nombre',
            'empresa',
            'empresa_nombre',
            'fecha_inicio',
            'fecha_completada',
            'fecha_actualizacion',
            'estado',
            'puntuacion_total',
            'observaciones_generales',
            'suma_porcentajes',
            'calificaciones_caracteristica'
        ]
        read_only_fields = [
            'id', 
            'codigo_evaluacion', 
            'evaluador', 
            'empresa',
            'fecha_inicio', 
            'fecha_actualizacion',
            'puntuacion_total'
        ]
    
    def get_suma_porcentajes(self, obj):
        """Devuelve la suma de porcentajes asignados"""
        return sum(cal.porcentaje_asignado for cal in obj.calificaciones_caracteristica.all())
    
    def validate(self, data):
        """Validaciones a nivel de evaluación"""
        software = data.get('software')
        user = self.context['request'].user
        
        # Validar que el software pertenece a la empresa del usuario
        if not hasattr(user, 'empresa') or not user.empresa:
            raise serializers.ValidationError("El usuario no tiene una empresa asignada.")
        
        if software and software.empresa != user.empresa:
            raise serializers.ValidationError({
                'software': 'El software seleccionado no pertenece a su empresa.'
            })
        
        return data
    
    def create(self, validated_data):
        # Asignar automáticamente evaluador y empresa
        user = self.context['request'].user
        validated_data['evaluador'] = user
        validated_data['empresa'] = user.empresa
        
        return super().create(validated_data)

# NUEVO: Serializer específico para el flujo del frontend
class EvaluacionCompletaFlexibleSerializer(serializers.Serializer):
    """
    Serializer para crear una evaluación completa siguiendo el flujo del frontend:
    1. Usuario elige una norma
    2. Se cargan todas las características
    3. Usuario asigna porcentajes a características (suma = 100%)
    4. Usuario elige subcaracterísticas por característica
    5. Usuario califica cada subcaracterística (0-3)
    6. Se calcula todo automáticamente
    """
    software = serializers.PrimaryKeyRelatedField(queryset=Software.objects.all())
    norma = serializers.PrimaryKeyRelatedField(queryset=Norma.objects.all())
    observaciones_generales = serializers.CharField(required=False, allow_blank=True)
    
    # Estructura para calificaciones con porcentajes dinámicos
    calificaciones = serializers.ListField(
        child=serializers.DictField(), 
        write_only=True,
        help_text="Lista de calificaciones por característica con porcentajes y subcaracterísticas seleccionadas"
    )
    
    def validate_calificaciones(self, value):
        """
        Validar estructura:
        [
            {
                "caracteristica_id": 1,
                "porcentaje_asignado": 30.5,
                "observaciones": "...",
                "subcaracteristicas": [
                    {
                        "subcaracteristica_id": 1,
                        "puntos": 3,
                        "observacion": "...",
                        "evidencia_url": "..."
                    }
                ]
            }
        ]
        """
        if not isinstance(value, list) or not value:
            raise serializers.ValidationError("Se requiere al menos una calificación.")
        
        # Validar que los porcentajes sumen 100%
        total_porcentaje = sum(cal.get('porcentaje_asignado', 0) for cal in value)
        if abs(total_porcentaje - 100) > 0.01:
            raise serializers.ValidationError(
                f"Los porcentajes de características deben sumar 100%. Actual: {total_porcentaje}%"
            )
        
        for idx, calificacion in enumerate(value):
            # Validar campos requeridos
            required_fields = ['caracteristica_id', 'porcentaje_asignado', 'subcaracteristicas']
            for field in required_fields:
                if field not in calificacion:
                    raise serializers.ValidationError(f"Calificación {idx}: falta '{field}'")
            
            # Validar porcentaje
            porcentaje = calificacion['porcentaje_asignado']
            if not isinstance(porcentaje, (int, float)) or porcentaje < 0 or porcentaje > 100:
                raise serializers.ValidationError(f"Calificación {idx}: porcentaje inválido")
            
            # Validar subcaracterísticas
            subcals = calificacion['subcaracteristicas']
            if not isinstance(subcals, list) or not subcals:
                raise serializers.ValidationError(f"Calificación {idx}: debe tener al menos una subcaracterística")
            
            for sub_idx, sub in enumerate(subcals):
                if 'subcaracteristica_id' not in sub or 'puntos' not in sub:
                    raise serializers.ValidationError(
                        f"Calificación {idx}, subcaracterística {sub_idx}: faltan campos requeridos"
                    )
                
                puntos = sub['puntos']
                if not isinstance(puntos, int) or puntos < 0 or puntos > 3:
                    raise serializers.ValidationError(
                        f"Calificación {idx}, subcaracterística {sub_idx}: puntos deben ser 0-3"
                    )
        
        return value
    
    def validate(self, data):
        """Validar consistencia entre norma y calificaciones"""
        norma = data.get('norma')
        calificaciones = data.get('calificaciones', [])
        
        if norma:
            # Verificar que las características existen en la norma
            caracteristicas_norma = set(norma.caracteristicas.values_list('id', flat=True))
            caracteristicas_evaluadas = set(cal['caracteristica_id'] for cal in calificaciones)
            
            invalidas = caracteristicas_evaluadas - caracteristicas_norma
            if invalidas:
                raise serializers.ValidationError(
                    f"Características inválidas para esta norma: {list(invalidas)}"
                )
            
            # Verificar subcaracterísticas
            for cal in calificaciones:
                caracteristica_id = cal['caracteristica_id']
                subcaracteristicas_validas = set(
                    SubCaracteristica.objects.filter(
                        caracteristica_id=caracteristica_id
                    ).values_list('id', flat=True)
                )
                
                subcaracteristicas_evaluadas = set(
                    sub['subcaracteristica_id'] for sub in cal['subcaracteristicas']
                )
                
                invalidas_sub = subcaracteristicas_evaluadas - subcaracteristicas_validas
                if invalidas_sub:
                    raise serializers.ValidationError(
                        f"Subcaracterísticas inválidas para característica {caracteristica_id}: {list(invalidas_sub)}"
                    )
        
        return data
    
    def create(self, validated_data):
        """Crear evaluación completa con transacción atómica"""
        from django.db import transaction
        
        calificaciones_data = validated_data.pop('calificaciones')
        user = self.context['request'].user
        
        with transaction.atomic():
            # Crear evaluación principal
            evaluacion = Evaluacion.objects.create(
                evaluador=user,
                empresa=user.empresa,
                **validated_data
            )
            
            # Crear calificaciones por característica
            for cal_data in calificaciones_data:
                caracteristica = Caracteristica.objects.get(id=cal_data['caracteristica_id'])
                
                cal_caracteristica = CalificacionCaracteristica.objects.create(
                    evaluacion=evaluacion,
                    caracteristica=caracteristica,
                    porcentaje_asignado=Decimal(str(cal_data['porcentaje_asignado'])),
                    puntuacion_obtenida=Decimal('0.00'),  # Se calculará después
                    observaciones=cal_data.get('observaciones', '')
                )
                
                # Crear calificaciones de subcaracterísticas
                for sub_data in cal_data['subcaracteristicas']:
                    CalificacionSubCaracteristica.objects.create(
                        calificacion_caracteristica=cal_caracteristica,
                        subcaracteristica_id=sub_data['subcaracteristica_id'],
                        puntos=sub_data['puntos'],
                        observacion=sub_data.get('observacion', ''),
                        evidencia_url=sub_data.get('evidencia_url', '')
                    )
                
                # Calcular y actualizar puntuación de la característica
                cal_caracteristica.puntuacion_obtenida = cal_caracteristica.calcular_puntuacion_caracteristica()
                cal_caracteristica.save()
            
            # Calcular puntuación total de la evaluación
            evaluacion.puntuacion_total = evaluacion.calcular_puntuacion_total()
            evaluacion.estado = 'completada'
            evaluacion.save()
            
            return evaluacion
    
    def to_representation(self, instance):
        """Usar EvaluacionSerializer para la respuesta"""
        return EvaluacionSerializer(instance, context=self.context).data

# Serializer para obtener estructura de norma para evaluación
class NormaParaEvaluacionSerializer(serializers.ModelSerializer):
    """
    Serializer para obtener la estructura de una norma para el frontend
    """
    caracteristicas = serializers.SerializerMethodField()
    
    class Meta:
        model = Norma
        fields = ['id', 'nombre', 'descripcion', 'version', 'caracteristicas']
    
    def get_caracteristicas(self, obj):
        """Obtener características con sus subcaracterísticas"""
        caracteristicas = obj.caracteristicas.all().order_by('orden')
        resultado = []
        
        for car in caracteristicas:
            subcaracteristicas = car.subcaracteristicas.all().order_by('orden')
            resultado.append({
                'id': car.id,
                'nombre': car.nombre,
                'descripcion': car.descripcion,
                'orden': car.orden,
                'subcaracteristicas': [
                    {
                        'id': sub.id,
                        'nombre': sub.nombre,
                        'descripcion': sub.descripcion,
                        'criterios_evaluacion': sub.criterios_evaluacion,
                        'orden': sub.orden
                    }
                    for sub in subcaracteristicas
                ]
            })
        
        return resultado