from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from datetime import datetime

from .models import Evaluacion, CalificacionCaracteristica, CalificacionSubCaracteristica
from .serializers import (
    EvaluacionSerializer, 
    CalificacionCaracteristicaSerializer,
    CalificacionSubCaracteristicaSerializer,
    EvaluacionCompletaFlexibleSerializer,  # NUEVO
    NormaParaEvaluacionSerializer
)
from .permissions import EvaluacionPermission
from software.models import Software
from normas.models import Norma
from rest_framework import serializers
from django.db.models import Count

class EvaluacionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar evaluaciones de software
    """
    serializer_class = EvaluacionSerializer
    permission_classes = [IsAuthenticated, EvaluacionPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'norma', 'software', 'empresa']
    search_fields = ['codigo_evaluacion', 'software__nombre', 'norma__nombre']
    ordering_fields = ['fecha_inicio', 'fecha_completada', 'puntuacion_total']
    ordering = ['-fecha_inicio']
    
    def get_queryset(self):
        """Filtrar evaluaciones según el rol del usuario"""
        user = self.request.user
        queryset = Evaluacion.objects.select_related(
            'software', 'norma', 'evaluador', 'empresa'
        ).prefetch_related(
            'calificaciones_caracteristica__calificaciones_subcaracteristica'
        )
        
        # Administradores ven todo
        if user.groups.filter(name='Administradores').exists():
            return queryset
        
        # Evaluadores ven evaluaciones de su empresa
        if user.groups.filter(name='Evaluadores').exists():
            return queryset.filter(empresa=user.empresa)
        
        # Usuarios empresa ven solo las suyas
        if user.groups.filter(name='Usuarios_Empresa').exists():
            return queryset.filter(evaluador=user)
        
        return queryset.none()
    
    def perform_create(self, serializer):
        """Asignar evaluador y empresa automáticamente"""
        user = self.request.user
        if not hasattr(user, 'empresa') or not user.empresa:
            raise serializers.ValidationError("El usuario no tiene una empresa asignada.")
        
        serializer.save(evaluador=user, empresa=user.empresa)
    
    @action(detail=True, methods=['post'])
    def completar(self, request, pk=None):
        """Marcar evaluación como completada y calcular puntuaciones"""
        evaluacion = self.get_object()
        
        if evaluacion.estado == 'completada':
            return Response(
                {'error': 'La evaluación ya está completada'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar que los porcentajes sumen 100%
        total_porcentaje = sum(
            cal.porcentaje_asignado for cal in evaluacion.calificaciones_caracteristica.all()
        )
        
        if abs(total_porcentaje - 100) > 0.01:
            return Response(
                {
                    'error': 'Los porcentajes de características deben sumar 100%',
                    'total_actual': float(total_porcentaje)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Recalcular todas las puntuaciones
        with transaction.atomic():
            for cal_caracteristica in evaluacion.calificaciones_caracteristica.all():
                cal_caracteristica.puntuacion_obtenida = cal_caracteristica.calcular_puntuacion_caracteristica()
                cal_caracteristica.save()
            
            evaluacion.puntuacion_total = evaluacion.calcular_puntuacion_total()
            evaluacion.estado = 'completada'
            evaluacion.fecha_completada = datetime.now()
            evaluacion.save()
        
        return Response({
            'message': 'Evaluación completada exitosamente',
            'puntuacion_total': evaluacion.puntuacion_total
        })
    
    @action(detail=True, methods=['get'])
    def reporte(self, request, pk=None):
        """Generar reporte detallado de la evaluación"""
        evaluacion = self.get_object()
        
        # Construir reporte con detalles por característica
        reporte_data = {
            'evaluacion': EvaluacionSerializer(evaluacion).data,
            'resumen_por_caracteristica': [],
            'estadisticas': {
                'total_subcaracteristicas': 0,
                'subcaracteristicas_excelente': 0,  # 3 puntos
                'subcaracteristicas_bueno': 0,      # 2 puntos  
                'subcaracteristicas_regular': 0,    # 1 punto
                'subcaracteristicas_deficiente': 0  # 0 puntos
            }
        }
        
        for cal_car in evaluacion.calificaciones_caracteristica.all():
            cal_subs = cal_car.calificaciones_subcaracteristica.all()
            
            caracteristica_info = {
                'caracteristica': cal_car.caracteristica.nombre,
                'porcentaje_asignado': cal_car.porcentaje_asignado,
                'puntuacion_obtenida': cal_car.puntuacion_obtenida,
                'numero_subcaracteristicas': cal_subs.count(),
                'detalle_subcaracteristicas': []
            }
            
            # Estadísticas por subcaracterística
            for cal_sub in cal_subs:
                reporte_data['estadisticas']['total_subcaracteristicas'] += 1
                
                if cal_sub.puntos == 3:
                    reporte_data['estadisticas']['subcaracteristicas_excelente'] += 1
                elif cal_sub.puntos == 2:
                    reporte_data['estadisticas']['subcaracteristicas_bueno'] += 1
                elif cal_sub.puntos == 1:
                    reporte_data['estadisticas']['subcaracteristicas_regular'] += 1
                else:
                    reporte_data['estadisticas']['subcaracteristicas_deficiente'] += 1
                
                caracteristica_info['detalle_subcaracteristicas'].append({
                    'nombre': cal_sub.subcaracteristica.nombre,
                    'puntos': cal_sub.puntos,
                    'porcentaje': cal_sub.porcentaje_obtenido,
                    'observacion': cal_sub.observacion
                })
            
            reporte_data['resumen_por_caracteristica'].append(caracteristica_info)
        
        return Response(reporte_data)

# NUEVA Vista específica para el flujo del frontend
class EvaluacionFlexibleView(APIView):
    """
    Vista para crear evaluaciones completas siguiendo el flujo del frontend
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Crear evaluación completa con estructura flexible:
        {
            "software": 1,
            "norma": 1,
            "observaciones_generales": "...",
            "calificaciones": [
                {
                    "caracteristica_id": 1,
                    "porcentaje_asignado": 40.0,
                    "observaciones": "...",
                    "subcaracteristicas": [
                        {
                            "subcaracteristica_id": 1,
                            "puntos": 3,
                            "observacion": "Excelente implementación",
                            "evidencia_url": "https://..."
                        },
                        {
                            "subcaracteristica_id": 3,
                            "puntos": 2,
                            "observacion": "Buena pero mejorable"
                        }
                    ]
                },
                {
                    "caracteristica_id": 2,
                    "porcentaje_asignado": 60.0,
                    "observaciones": "...",
                    "subcaracteristicas": [
                        {
                            "subcaracteristica_id": 4,
                            "puntos": 1,
                            "observacion": "Necesita mejoras"
                        }
                    ]
                }
            ]
        }
        """
        serializer = EvaluacionCompletaFlexibleSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                evaluacion = serializer.save()
                return Response(
                    {
                        'message': 'Evaluación creada exitosamente',
                        'evaluacion': EvaluacionSerializer(evaluacion, context={'request': request}).data
                    },
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {'error': f'Error al crear la evaluación: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(
            {'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

class NormaParaEvaluacionView(APIView):
    """
    Vista para obtener la estructura de una norma para evaluación
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, norma_id):
        """
        Obtener estructura completa de una norma para el frontend:
        - Todas las características con sus subcaracterísticas
        - Sin porcentajes predefinidos (el usuario los asigna)
        """
        try:
            norma = Norma.objects.prefetch_related(
                'caracteristicas__subcaracteristicas'
            ).get(id=norma_id)
        except Norma.DoesNotExist:
            return Response(
                {'error': 'Norma no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = NormaParaEvaluacionSerializer(norma)
        return Response(serializer.data)

class ValidarPorcentajesView(APIView):
    """
    Vista para validar que los porcentajes sumen 100%
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Validar porcentajes antes de enviar la evaluación:
        {
            "porcentajes": [
                {"caracteristica_id": 1, "porcentaje": 40.0},
                {"caracteristica_id": 2, "porcentaje": 60.0}
            ]
        }
        """
        porcentajes = request.data.get('porcentajes', [])
        
        if not isinstance(porcentajes, list):
            return Response(
                {'error': 'Se esperaba una lista de porcentajes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        total = sum(p.get('porcentaje', 0) for p in porcentajes)
        es_valido = abs(total - 100) <= 0.01
        
        return Response({
            'es_valido': es_valido,
            'total_porcentaje': round(total, 2),
            'diferencia': round(100 - total, 2),
            'message': 'Porcentajes válidos' if es_valido else f'Los porcentajes suman {total}%, no 100%'
        })

class CalificacionCaracteristicaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar calificaciones de características
    """
    serializer_class = CalificacionCaracteristicaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['evaluacion', 'caracteristica']
    
    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Administradores').exists():
            return CalificacionCaracteristica.objects.all()
        
        return CalificacionCaracteristica.objects.filter(
            evaluacion__empresa=user.empresa
        )

class CalificacionSubCaracteristicaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar calificaciones de subcaracterísticas
    """
    serializer_class = CalificacionSubCaracteristicaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['calificacion_caracteristica', 'subcaracteristica']
    
    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Administradores').exists():
            return CalificacionSubCaracteristica.objects.all()
        
        return CalificacionSubCaracteristica.objects.filter(
            calificacion_caracteristica__evaluacion__empresa=user.empresa
        )

class MisSoftwaresView(APIView):
    """
    Vista para obtener los softwares de la empresa del usuario
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtener softwares disponibles para evaluación"""
        user = request.user
        
        if not hasattr(user, 'empresa') or not user.empresa:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener softwares de la empresa
        softwares = Software.objects.filter(empresa=user.empresa)
        
        # Incluir información de evaluaciones existentes
        software_data = []
        for software in softwares:
            evaluaciones = software.evaluaciones.all()
            software_info = {
                'id': software.id,
                'nombre': software.nombre,
                'version': software.vesion,
                'codigo_software': software.codigo_software,
                'url': software.url,
                'numero_evaluaciones': evaluaciones.count(),
                'ultima_evaluacion': None
            }
            
            if evaluaciones.exists():
                ultima = evaluaciones.order_by('-fecha_inicio').first()
                software_info['ultima_evaluacion'] = {
                    'codigo': ultima.codigo_evaluacion,
                    'fecha': ultima.fecha_inicio,
                    'estado': ultima.estado,
                    'puntuacion': ultima.puntuacion_total
                }
            
            software_data.append(software_info)
        
        return Response({
            'empresa': user.empresa.nombre,
            'softwares': software_data
        })

class NormasDisponiblesView(APIView):
    """
    Vista para obtener las normas disponibles para evaluación
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obtener normas aprobadas disponibles"""
        normas = Norma.objects.filter(estado='aprobada').annotate(
            numero_caracteristicas=Count('caracteristicas')
        )
        
        normas_data = []
        for norma in normas:
            normas_data.append({
                'id': norma.id,
                'nombre': norma.nombre,
                'descripcion': norma.descripcion,
                'version': norma.version,
                'numero_caracteristicas': norma.numero_caracteristicas,
                'fecha_creacion': norma.fecha_creacion
            })
        
        return Response({
            'normas_disponibles': normas_data,
            'total': len(normas_data)
        })

class EstadisticasEmpresaView(APIView):
    """
    Vista para obtener estadísticas de evaluaciones de la empresa
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Estadísticas generales de evaluaciones de la empresa"""
        user = request.user
        
        if not hasattr(user, 'empresa') or not user.empresa:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        evaluaciones = Evaluacion.objects.filter(empresa=user.empresa)
        
        estadisticas = {
            'total_evaluaciones': evaluaciones.count(),
            'evaluaciones_completadas': evaluaciones.filter(estado='completada').count(),
            'evaluaciones_en_progreso': evaluaciones.filter(estado='en_progreso').count(),
            'evaluaciones_borrador': evaluaciones.filter(estado='borrador').count(),
            'puntuacion_promedio': None,
            'softwares_evaluados': evaluaciones.values('software').distinct().count(),
            'normas_utilizadas': evaluaciones.values('norma').distinct().count(),
            'top_softwares': [],
            'areas_mejora': []
        }
        
        # Calcular puntuación promedio de evaluaciones completadas
        completadas = evaluaciones.filter(
            estado='completada',
            puntuacion_total__isnull=False
        )
        
        if completadas.exists():
            from django.db.models import Avg
            promedio = completadas.aggregate(Avg('puntuacion_total'))['puntuacion_total__avg']
            estadisticas['puntuacion_promedio'] = round(float(promedio), 2) if promedio else None
        
        # Top 5 softwares mejor calificados
        top_softwares = completadas.select_related('software').order_by('-puntuacion_total')[:5]
        estadisticas['top_softwares'] = [
            {
                'software': eval.software.nombre,
                'puntuacion': float(eval.puntuacion_total),
                'codigo_evaluacion': eval.codigo_evaluacion
            }
            for eval in top_softwares
        ]
        
        # Áreas de mejora (características con menor puntuación promedio)
        from django.db.models import Avg
        areas_mejora = CalificacionCaracteristica.objects.filter(
            evaluacion__empresa=user.empresa,
            evaluacion__estado='completada'
        ).values(
            'caracteristica__nombre'
        ).annotate(
            promedio=Avg('puntuacion_obtenida')
        ).order_by('promedio')[:5]
        
        estadisticas['areas_mejora'] = [
            {
                'caracteristica': area['caracteristica__nombre'],
                'puntuacion_promedio': round(float(area['promedio']), 2)
            }
            for area in areas_mejora
        ]
        
        return Response(estadisticas)