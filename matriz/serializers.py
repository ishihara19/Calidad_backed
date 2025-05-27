# matriz/serializers.py
from rest_framework import serializers
from .models import MatrizRiesgo, RiesgoMatriz, CausaRiesgo, ParametroMatriz, AuditoriaMatriz
from django.db import transaction

class CausaRiesgoSerializer(serializers.ModelSerializer):
    """Serializer para las causas de riesgo"""
    
    class Meta:
        model = CausaRiesgo
        fields = ['id', 'causa', 'factor', 'controles', 'orden']
    
    def validate_causa(self, value):
        if not value.strip():
            raise serializers.ValidationError("La descripción de la causa no puede estar vacía.")
        return value


class RiesgoMatrizSerializer(serializers.ModelSerializer):
    """Serializer para los riesgos individuales"""
    
    causas = CausaRiesgoSerializer(many=True, required=False)
    zona_riesgo = serializers.ReadOnlyField(source='calcular_zona_riesgo')
    
    class Meta:
        model = RiesgoMatriz
        fields = [
            'id', 'numero', 'fecha', 'codigo', 'nombre', 'descripcion',
            'efectos', 'tipo_riesgo', 'probabilidad', 'impacto',
            'controles_existentes', 'tipo_control', 'efectividad_control',
            'controles_evaluacion', 'tratamiento', 'responsable_control',
            'aceptado', 'causas', 'zona_riesgo'
        ]
    
    def validate_nombre(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre del riesgo es obligatorio.")
        return value
    
    def validate_numero(self, value):
        matriz_id = self.context.get('matriz_id')
        if matriz_id and self.instance is None:  # Solo para creación
            if RiesgoMatriz.objects.filter(matriz_id=matriz_id, numero=value).exists():
                raise serializers.ValidationError("Ya existe un riesgo con este número en la matriz.")
        return value
    
    def create(self, validated_data):
        causas_data = validated_data.pop('causas', [])
        riesgo = RiesgoMatriz.objects.create(**validated_data)
        
        # Crear causas
        for orden, causa_data in enumerate(causas_data, 1):
            causa_data['orden'] = orden
            CausaRiesgo.objects.create(riesgo=riesgo, **causa_data)
        
        return riesgo
    
    def update(self, instance, validated_data):
        causas_data = validated_data.pop('causas', [])
        
        # Actualizar campos del riesgo
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Actualizar causas si se proporcionaron
        if causas_data:
            instance.causas.all().delete()
            for orden, causa_data in enumerate(causas_data, 1):
                causa_data['orden'] = orden
                CausaRiesgo.objects.create(riesgo=instance, **causa_data)
        
        return instance

# matriz/serializers.py - VERSIÓN SIMPLIFICADA TEMPORAL

from rest_framework import serializers
from .models import MatrizRiesgo
from django.db import transaction

class MatrizRiesgoSerializer(serializers.ModelSerializer):
    """Serializer simplificado para debugging"""
    
    class Meta:
        model = MatrizRiesgo
        fields = [
            'id', 'nombre', 'descripcion', 'responsable', 'fecha_creacion',
            'fecha_modificacion'
        ]
        read_only_fields = ['id', 'fecha_modificacion']
    
    def validate_nombre(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre de la matriz es obligatorio.")
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        
        # Debug: imprimir datos recibidos
        print("📝 Datos recibidos:", validated_data)
        print("👤 Usuario:", request.user if request else 'No request')
        
        # Asignar usuario y empresa automáticamente
        if request and hasattr(request, 'user'):
            validated_data['creado_por'] = request.user
            
            if hasattr(request.user, 'empresa') and request.user.empresa:
                validated_data['empresa'] = request.user.empresa
                print("🏢 Empresa asignada:", request.user.empresa)
            else:
                print("❌ Usuario sin empresa")
                raise serializers.ValidationError("El usuario no tiene una empresa asignada.")
        
        # Asegurar que fecha_creacion sea un objeto date
        if 'fecha_creacion' in validated_data:
            from datetime import datetime, date
            fecha = validated_data['fecha_creacion']
            if isinstance(fecha, str):
                validated_data['fecha_creacion'] = datetime.strptime(fecha, '%Y-%m-%d').date()
            elif isinstance(fecha, datetime):
                validated_data['fecha_creacion'] = fecha.date()
        else:
            validated_data['fecha_creacion'] = date.today()
        
        print("💾 Intentando crear matriz...")
        try:
            matriz = MatrizRiesgo.objects.create(**validated_data)
            print("✅ Matriz creada exitosamente:", matriz.id)
            return matriz
        except Exception as e:
            print("❌ Error creando matriz:", str(e))
            raise serializers.ValidationError(f"Error al crear matriz: {str(e)}")

# Comentar temporalmente otros serializers complejos para evitar conflictos


class MatrizRiesgoListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listas de matrices"""
    
    total_riesgos = serializers.ReadOnlyField()
    resumen_riesgos_por_nivel = serializers.ReadOnlyField()
    creado_por_nombre = serializers.CharField(source='creado_por.get_full_name', read_only=True)
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    
    class Meta:
        model = MatrizRiesgo
        fields = [
            'id', 'nombre', 'descripcion', 'responsable', 'fecha_creacion',
            'fecha_modificacion', 'creado_por_nombre', 'empresa_nombre',
            'total_riesgos', 'resumen_riesgos_por_nivel'
        ]


class ParametroMatrizSerializer(serializers.ModelSerializer):
    """Serializer para los parámetros del sistema"""
    
    class Meta:
        model = ParametroMatriz
        fields = ['id', 'tipo', 'valor', 'etiqueta', 'descripcion', 'activo']


class AuditoriaMatrizSerializer(serializers.ModelSerializer):
    """Serializer para el registro de auditoría"""
    
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    matriz_nombre = serializers.CharField(source='matriz.nombre', read_only=True)
    
    class Meta:
        model = AuditoriaMatriz
        fields = [
            'id', 'matriz', 'matriz_nombre', 'usuario', 'usuario_nombre',
            'accion', 'descripcion', 'fecha_accion', 'datos_anteriores', 'datos_nuevos'
        ]
        read_only_fields = ['id', 'fecha_accion']


# Serializer especial para el frontend
class MatrizRiesgoFrontendSerializer(serializers.ModelSerializer):
    """
    Serializer especial que coincide con la estructura del frontend.
    Maneja la estructura específica que espera el componente React.
    """
    
    # Para compatibilidad con el frontend
    fechaCreacion = serializers.DateField(source='fecha_creacion')
    fechaModificacion = serializers.DateTimeField(source='fecha_modificacion', read_only=True)
    
    class Meta:
        model = MatrizRiesgo
        fields = [
            'id', 'nombre', 'descripcion', 'responsable', 
            'fechaCreacion', 'fechaModificacion', 'riesgos'
        ]
    
    def to_representation(self, instance):
        """Personalizar la representación para el frontend"""
        data = super().to_representation(instance)
        
        # Convertir riesgos al formato esperado por el frontend
        riesgos_frontend = []
        for riesgo in instance.riesgos.all():
            riesgo_data = {
                'id': riesgo.id,
                'numero': riesgo.numero,
                'fecha': riesgo.fecha,
                'codigo': riesgo.codigo,
                'nombre': riesgo.nombre,
                'descripcion': riesgo.descripcion,
                'causas': [
                    {
                        'causa': causa.causa,
                        'factor': causa.factor,
                        'controles': causa.controles
                    }
                    for causa in riesgo.causas.all()
                ],
                'efectos': riesgo.efectos,
                'tipoRiesgo': riesgo.tipo_riesgo,
                'probabilidad': riesgo.probabilidad,
                'impacto': riesgo.impacto,
                'controlesExistentes': riesgo.controles_existentes,
                'tipoControl': riesgo.tipo_control,
                'efectividadControl': riesgo.efectividad_control,
                'controlesEvaluacion': riesgo.controles_evaluacion,
                'tratamiento': riesgo.tratamiento,
                'responsableControl': riesgo.responsable_control,
                'aceptado': riesgo.aceptado,
                'zonaRiesgo': riesgo.calcular_zona_riesgo()
            }
            riesgos_frontend.append(riesgo_data)
        
        data['riesgos'] = riesgos_frontend
        return data
    
    def create(self, validated_data):
        """Crear matriz desde el frontend"""
        riesgos_data = self.initial_data.get('riesgos', [])
        request = self.context.get('request')
        
        # Asignar usuario y empresa
        if request and hasattr(request, 'user'):
            validated_data['creado_por'] = request.user
            if hasattr(request.user, 'empresa') and request.user.empresa:
                validated_data['empresa'] = request.user.empresa
            else:
                raise serializers.ValidationError("El usuario no tiene una empresa asignada.")
        
        with transaction.atomic():
            matriz = MatrizRiesgo.objects.create(**validated_data)
            
            # Procesar riesgos del frontend
            for riesgo_data in riesgos_data:
                causas_data = riesgo_data.pop('causas', [])
                
                # Mapear campos del frontend al modelo
                riesgo_modelo = {
                    'matriz': matriz,
                    'numero': riesgo_data.get('numero'),
                    'fecha': riesgo_data.get('fecha'),
                    'codigo': riesgo_data.get('codigo', ''),
                    'nombre': riesgo_data.get('nombre'),
                    'descripcion': riesgo_data.get('descripcion', ''),
                    'efectos': riesgo_data.get('efectos', ''),
                    'tipo_riesgo': riesgo_data.get('tipoRiesgo', ''),
                    'probabilidad': riesgo_data.get('probabilidad', 1),
                    'impacto': riesgo_data.get('impacto', 1),
                    'controles_existentes': riesgo_data.get('controlesExistentes', ''),
                    'tipo_control': riesgo_data.get('tipoControl', 'Preventivo'),
                    'efectividad_control': riesgo_data.get('efectividadControl', 0),
                    'controles_evaluacion': riesgo_data.get('controlesEvaluacion', {}),
                    'tratamiento': riesgo_data.get('tratamiento', ''),
                    'responsable_control': riesgo_data.get('responsableControl', ''),
                    'aceptado': riesgo_data.get('aceptado', False)
                }
                
                riesgo = RiesgoMatriz.objects.create(**riesgo_modelo)
                
                # Crear causas
                for orden, causa_data in enumerate(causas_data, 1):
                    CausaRiesgo.objects.create(
                        riesgo=riesgo,
                        causa=causa_data.get('causa', ''),
                        factor=causa_data.get('factor', ''),
                        controles=causa_data.get('controles', ''),
                        orden=orden
                    )
        
        return matriz