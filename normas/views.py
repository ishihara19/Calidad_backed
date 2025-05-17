from rest_framework import viewsets
from .models import Norma, Caracteristica, SubCaracteristica, CalificacionSubCaracteristica
from .serializers import NormaSerializer, CaracteristicaSerializer, SubCaracteristicaSerializer, CalificacionSubCaracteristicaSerializer

class NormaViewSet(viewsets.ModelViewSet):
    queryset = Norma.objects.all()
    serializer_class = NormaSerializer

class CaracteristicaViewSet(viewsets.ModelViewSet):
    queryset = Caracteristica.objects.all()
    serializer_class = CaracteristicaSerializer

class SubCaracteristicaViewSet(viewsets.ModelViewSet):
    queryset = SubCaracteristica.objects.all()
    serializer_class = SubCaracteristicaSerializer

class CalificacionSubCaracteristicaViewSet(viewsets.ModelViewSet):
    queryset = CalificacionSubCaracteristica.objects.all()
    serializer_class = CalificacionSubCaracteristicaSerializer
