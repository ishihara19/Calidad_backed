from rest_framework import serializers
from .models import Norma, Caracteristica, SubCaracteristica, CalificacionSubCaracteristica

class CalificacionSubCaracteristicaSerializer(serializers.ModelSerializer):
    subcaracteristica = serializers.PrimaryKeyRelatedField(
        queryset=SubCaracteristica.objects.all(),
        help_text="ID de la subcaracterística a calificar."
    )
    class Meta:
        model = CalificacionSubCaracteristica
        fields = [
            'id', 
            'subcaracteristica', 
            'observacion', 
            'puntos', 
            'codigo_calificacion', # Se incluirá en la respuesta
            'usuario',             # Se incluirá en la respuesta
            'empresa',             # Se incluirá en la respuesta
            'fecha_cracion'        # Se incluirá en la respuesta
        ]
        read_only_fields = [
            'id', 
            'codigo_calificacion', 
            'usuario',
            'empresa',               
            'fecha_cracion'
        ]
        
        def validate_puntos(self, value):
            if value < 0 or value > 3:
                raise serializers.ValidationError("Los puntos deben estar entre 0 y 3.")
            return value 
    

class SubCaracteristicaSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SubCaracteristica
        fields = ['id', 'caracteristica', 'nombre', 'descripcion',]

class CaracteristicaSerializer(serializers.ModelSerializer):
    subcaracteristicas = SubCaracteristicaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Caracteristica
        fields = ['id', 'norma', 'nombre', 'descripcion', 'subcaracteristicas']

class NormaSerializer(serializers.ModelSerializer):
    caracteristicas = CaracteristicaSerializer(many=True, read_only=True)

    class Meta:
        model = Norma
        fields = ['id', 'nombre', 'descripcion', 'caracteristicas']
