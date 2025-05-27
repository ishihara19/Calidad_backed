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
    EvaluacionCompletaSerializer
)
from .permissions import EvaluacionPermission
from software.models import Software

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
        
        # Verificar que todas las características obligatorias estén calificadas
        caracteristicas_obligatorias = evaluacion.norma.caracteristicas.filter(es_obligatoria=True)
        calificaciones_existentes = evaluacion.calificaciones_caracteristica.values_list(
            'caracteristica_id', flat=True
        )
        
        faltantes = caracteristicas_obligatorias.exclude(id__in=calificaciones_existentes)
        if faltantes.exists():
            return Response(
                {
                    'error': 'Faltan calificaciones para características obligatorias',
                    'caracteristicas_faltantes': list(faltantes.values_list('nombre', flat=True))
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
                'porcentaje_peso': cal_car.caracteristica.porcentaje_peso,
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

class EvaluacionCompletaView(APIView):
    """
    Vista para crear evaluaciones completas con todas las calificaciones
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Crear evaluación completa con estructura:
        {
            "software": 1,
            "norma": 1,
            "observaciones_generales": "...",
            "calificaciones": [
                {
                    "caracteristica_id": 1,
                    "observaciones": "...",
                    "subcaracteristicas": [
                        {
                            "subcaracteristica_id": 1,
                            "puntos": 3,
                            "observacion": "Excelente implementación",
                            "evidencia_url": "https://..."
                        },
                        {
                            "subcaracteristica_id": 2,
                            "puntos": 2,
                            "observacion": "Buena pero mejorable"
                        }
                    ]
                }
            ]
        }
        """
        serializer = EvaluacionCompletaSerializer(
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