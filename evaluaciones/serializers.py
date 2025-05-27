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
    caracteristica_porcentaje = serializers.DecimalField(
        source='caracteristica.porcentaje_peso', 
        max_digits=5, 
        decimal_places=2, 
        read_only=True
    )
    calificaciones_subcaracteristica = CalificacionSubCaracteristicaSerializer(many=True, read_only=True)
    
    class Meta:
        model = CalificacionCaracteristica
        fields = [
            'id',
            'caracteristica',
            'caracteristica_nombre',
            'caracteristica_porcentaje',
            'puntuacion_obtenida',
            'puntuacion_maxima',
            'observaciones',
            'fecha_calificacion',
            'calificaciones_subcaracteristica'
        ]
        read_only_fields = ['id', 'fecha_calificacion', 'puntuacion_maxima']
    
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

class EvaluacionCompletaSerializer(serializers.Serializer):
    """
    Serializer para crear una evaluación completa con todas sus calificaciones
    """
    software = serializers.PrimaryKeyRelatedField(queryset=Software.objects.all())
    norma = serializers.PrimaryKeyRelatedField(queryset=Norma.objects.all())
    observaciones_generales = serializers.CharField(required=False, allow_blank=True)
    
    # Estructura anidada para calificaciones
    calificaciones = serializers.ListField(
        child=serializers.DictField(), 
        write_only=True,
        help_text="Lista de calificaciones por característica"
    )
    
    def validate_calificaciones(self, value):
        """
        Valida que las calificaciones tengan la estructura correcta
        """
        if not isinstance(value, list) or not value:
            raise serializers.ValidationError("Se requiere al menos una calificación.")
        
        for idx, calificacion in enumerate(value):
            if 'caracteristica_id' not in calificacion:
                raise serializers.ValidationError(f"Calificación {idx}: falta 'caracteristica_id'")
            
            if 'subcaracteristicas' not in calificacion:
                raise serializers.ValidationError(f"Calificación {idx}: falta 'subcaracteristicas'")
            
            # Validar subcaracterísticas
            for sub_idx, sub in enumerate(calificacion['subcaracteristicas']):
                if 'subcaracteristica_id' not in sub or 'puntos' not in sub:
                    raise serializers.ValidationError(
                        f"Calificación {idx}, subcaracterística {sub_idx}: faltan campos requeridos"
                    )
        
        return value
    
    def validate(self, data):
        """Validar consistencia entre norma y calificaciones"""
        norma = data.get('norma')
        calificaciones = data.get('calificaciones', [])
        
        if norma:
            # Validar que todas las características obligatorias estén incluidas
            caracteristicas_obligatorias = set(
                norma.caracteristicas.filter(es_obligatoria=True).values_list('id', flat=True)
            )
            caracteristicas_evaluadas = set(
                cal['caracteristica_id'] for cal in calificaciones
            )
            
            faltantes = caracteristicas_obligatorias - caracteristicas_evaluadas
            if faltantes:
                raise serializers.ValidationError(
                    f"Faltan calificaciones para características obligatorias: {list(faltantes)}"
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