from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Prefetch
from .models import Norma, Caracteristica, SubCaracteristica
from .serializers import (
    # Serializers simples
    NormaSimpleSerializer, CaracteristicaSimpleSerializer, SubCaracteristicaSimpleSerializer,
    # Serializers detallados
    NormaDetailSerializer, CaracteristicaDetailSerializer, SubCaracteristicaDetailSerializer,
    # Serializers de lista
    NormaListSerializer, CaracteristicaListSerializer,
    # Serializers especiales
    NormaPlantillaSerializer, ValidarPorcentajesSerializer
)
from .permissions import IsAdminOrReadOnly, CanManageNorma
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
class NormaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanManageNorma]
    
    def get_queryset(self):
        """Queryset optimizado según la acción"""
        base_queryset = Norma.objects.select_related('creado_por')
        
        if self.action == 'list':
            # Para listados: solo contar características (sin cargar datos)
            return base_queryset.annotate(
                numero_caracteristicas=Count('caracteristicas')
            )
        
        elif self.action == 'retrieve':
            # Para detalle: prefetch completo optimizado
            return base_queryset.prefetch_related(
                Prefetch(
                    'caracteristicas',
                    queryset=Caracteristica.objects.order_by('orden').prefetch_related(
                        Prefetch(
                            'subcaracteristicas',
                            queryset=SubCaracteristica.objects.order_by('orden')
                        )
                    )
                )
            )
        
        elif self.action == 'plantilla_evaluacion':
            # Para plantillas: solo características y subcaracterísticas obligatorias
            return base_queryset.prefetch_related(
                Prefetch(
                    'caracteristicas',
                    queryset=Caracteristica.objects.filter(es_obligatoria=True).order_by('orden').prefetch_related(
                        Prefetch(
                            'subcaracteristicas',
                            queryset=SubCaracteristica.objects.filter(es_obligatoria=True).order_by('orden')
                        )
                    )
                )
            )
        
        return base_queryset
    
    def get_serializer_class(self):
        """Serializer dinámico según la acción"""
        if self.action == 'list':
            return NormaListSerializer
        elif self.action == 'retrieve':
            return NormaDetailSerializer
        elif self.action == 'plantilla_evaluacion':
            return NormaPlantillaSerializer
        return NormaSimpleSerializer
    
    @action(detail=True, methods=['get'])
    def plantilla_evaluacion(self, request, pk=None):
        """Obtener plantilla optimizada para evaluación"""
        norma = self.get_object()
        serializer = self.get_serializer(norma)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def validar_porcentajes(self, request, pk=None):
        """Validar que los porcentajes sumen 100%"""
        norma = self.get_object()
        
        total_porcentaje = sum(
            car.porcentaje_peso for car in norma.caracteristicas.all()
        )
        
        es_valido = abs(total_porcentaje - 100.00) < 0.01
        
        return Response({
            'es_valido': es_valido,
            'total_porcentaje': float(total_porcentaje),
            'diferencia': float(100.00 - total_porcentaje),
            'message': 'Porcentajes válidos' if es_valido else f'Los porcentajes suman {total_porcentaje}%, no 100%'
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas generales de normas"""
        estadisticas = {
            'total_normas': Norma.objects.count(),
            'normas_aprobadas': Norma.objects.filter(estado='aprobada').count(),
            'normas_borrador': Norma.objects.filter(estado='borrador').count(),
            'total_caracteristicas': Caracteristica.objects.count(),
            'total_subcaracteristicas': SubCaracteristica.objects.count(),
        }
        
        # Top normas más utilizadas (si tienes evaluaciones)
        try:
            from evaluaciones.models import Evaluacion
            normas_utilizadas = Evaluacion.objects.values(
                'norma__nombre'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            estadisticas['normas_mas_utilizadas'] = list(normas_utilizadas)
        except ImportError:
            estadisticas['normas_mas_utilizadas'] = []
        
        return Response(estadisticas)

class CaracteristicaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        base_queryset = Caracteristica.objects.select_related('norma')
        
        if self.action == 'list':
            return base_queryset.annotate(
                numero_subcaracteristicas=Count('subcaracteristicas')
            )
        elif self.action == 'retrieve':
            return base_queryset.prefetch_related('subcaracteristicas')
        
        return base_queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CaracteristicaListSerializer
        elif self.action == 'retrieve':
            return CaracteristicaDetailSerializer
        return CaracteristicaSimpleSerializer
    
    @action(detail=True, methods=['get'])
    def subcaracteristicas(self, request, pk=None):
        """Obtener solo las subcaracterísticas de esta característica"""
        caracteristica = self.get_object()
        subcaracteristicas = caracteristica.subcaracteristicas.order_by('orden')
        
        serializer = SubCaracteristicaSimpleSerializer(subcaracteristicas, many=True)
        return Response({
            'caracteristica': caracteristica.nombre,
            'subcaracteristicas': serializer.data
        })

class SubCaracteristicaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        return SubCaracteristica.objects.select_related(
            'caracteristica__norma'
        ).order_by('caracteristica__orden', 'orden')
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return SubCaracteristicaDetailSerializer
        return SubCaracteristicaSimpleSerializer
    
    def list(self, request, *args, **kwargs):
        """Listado optimizado con filtros"""
        queryset = self.get_queryset()
        
        # Filtros opcionales
        caracteristica_id = request.query_params.get('caracteristica')
        norma_id = request.query_params.get('norma')
        solo_obligatorias = request.query_params.get('obligatorias') == 'true'
        
        if caracteristica_id:
            queryset = queryset.filter(caracteristica_id=caracteristica_id)
        if norma_id:
            queryset = queryset.filter(caracteristica__norma_id=norma_id)
        if solo_obligatorias:
            queryset = queryset.filter(es_obligatoria=True)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

# ✅ VISTA ADICIONAL PARA CASOS ESPECÍFICOS
class NormasPlantillasView(APIView):
    """Vista específica para obtener plantillas de evaluación de múltiples normas"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtener plantillas de todas las normas aprobadas"""
        normas = Norma.objects.filter(
            estado='aprobada'
        ).prefetch_related(
            Prefetch(
                'caracteristicas',
                queryset=Caracteristica.objects.filter(es_obligatoria=True).order_by('orden').prefetch_related(
                    Prefetch(
                        'subcaracteristicas',
                        queryset=SubCaracteristica.objects.filter(es_obligatoria=True).order_by('orden')
                    )
                )
            )
        )
        
        serializer = NormaPlantillaSerializer(normas, many=True)
        return Response({
            'plantillas_disponibles': serializer.data,
            'total_normas': normas.count()
        })