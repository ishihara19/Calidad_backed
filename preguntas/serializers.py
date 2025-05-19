from rest_framework import serializers
from .models import *

class PreguntaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pregunta
        fields = '__all__'

class SubcaracteristicaSerializer(serializers.ModelSerializer):
    preguntas = PreguntaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Subcaracteristica
        fields = '__all__'

class CaracteristicaSerializer(serializers.ModelSerializer):
    subcaracteristicas = SubcaracteristicaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Caracteristica
        fields = '__all__'

class RespuestaPreguntaSerializer(serializers.ModelSerializer):
    pregunta_texto = serializers.ReadOnlyField(source='pregunta.texto')
    
    class Meta:
        model = RespuestaPregunta
        fields = '__all__'

class EvaluacionSerializer(serializers.ModelSerializer):
    respuestas = RespuestaPreguntaSerializer(many=True, read_only=True)
    porcentaje_total = serializers.SerializerMethodField()
    nivel_cumplimiento = serializers.SerializerMethodField()
    
    class Meta:
        model = Evaluacion
        fields = '__all__'
    
    def get_porcentaje_total(self, obj):
        return obj.calcular_porcentaje_total()
    
    def get_nivel_cumplimiento(self, obj):
        return obj.obtener_nivel_cumplimiento()

class ProyectoSerializer(serializers.ModelSerializer):
    evaluaciones = EvaluacionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Proyecto
        fields = '__all__'