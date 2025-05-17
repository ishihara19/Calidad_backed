from rest_framework import serializers
from .models import Norma, Caracteristica, SubCaracteristica, CalificacionSubCaracteristica

class CalificacionSubCaracteristicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalificacionSubCaracteristica
        fields = "__all__"
        read_only_fields = ['id', 'valor_maximo']
    
    def validate(self, data):
        if data["puntos"] > data["valor_maximo"]:
            raise serializers.ValidationError("Los puntos no puden ser mayores que el valor maximo")
        if data["puntos"] < 0:
            raise serializers.ValidationError("Los puntos no puden ser menores que 0")
        
        return data   

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
