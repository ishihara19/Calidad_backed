from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count, Sum, F, Q
from django.shortcuts import get_object_or_404
from .models import (
    Caracteristica,
    Subcaracteristica,
    Pregunta,
    Proyecto,
    Evaluacion,
    RespuestaPregunta
)
from .serializers import (
    CaracteristicaSerializer,
    SubcaracteristicaSerializer,
    PreguntaSerializer,
    ProyectoSerializer,
    EvaluacionSerializer,
    RespuestaPreguntaSerializer
)


class CaracteristicaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar Características de ISO 25000.
    """
    queryset = Caracteristica.objects.all().order_by('codigo')
    serializer_class = CaracteristicaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['codigo']
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['codigo', 'nombre']


class SubcaracteristicaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar Subcaracterísticas de ISO 25000.
    """
    queryset = Subcaracteristica.objects.all().order_by('caracteristica__codigo', 'codigo')
    serializer_class = SubcaracteristicaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['caracteristica', 'codigo']
    search_fields = ['nombre', 'descripcion', 'caracteristica__nombre']
    ordering_fields = ['codigo', 'nombre', 'caracteristica__codigo']


class PreguntaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar Preguntas de evaluación.
    """
    queryset = Pregunta.objects.all().order_by('subcaracteristica__caracteristica__codigo', 
                                              'subcaracteristica__codigo', 'codigo')
    serializer_class = PreguntaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['subcaracteristica', 'subcaracteristica__caracteristica']
    search_fields = ['texto', 'codigo', 'subcaracteristica__nombre']
    ordering_fields = ['codigo', 'subcaracteristica__codigo']


class ProyectoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar Proyectos a evaluar.
    """
    serializer_class = ProyectoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'fecha_creacion']

    def get_queryset(self):
        """
        Filtra para que los usuarios solo vean sus propios proyectos, excepto los superusuarios.
        """
        if self.request.user.is_superuser:
            return Proyecto.objects.all()
        return Proyecto.objects.filter(propietario=self.request.user)
    
    def perform_create(self, serializer):
        # Establece automáticamente al usuario actual como propietario
        serializer.save(propietario=self.request.user)
    
    @action(detail=True, methods=['get'])
    def estadisticas(self, request, pk=None):
        """
        Obtiene estadísticas del proyecto incluyendo resultados de evaluaciones.
        """
        proyecto = self.get_object()
        evaluaciones = proyecto.evaluaciones.all()
        
        # Calcula estadísticas generales
        num_evaluaciones = evaluaciones.count()
        evaluaciones_completadas = evaluaciones.filter(estado='completada').count()
        
        # Calcula promedios de cumplimiento por característica
        caracteristicas_stats = []
        for caracteristica in Caracteristica.objects.all():
            preguntas_ids = Pregunta.objects.filter(
                subcaracteristica__caracteristica=caracteristica
            ).values_list('id', flat=True)
            
            # Obtiene todas las respuestas relacionadas con esta característica
            respuestas = RespuestaPregunta.objects.filter(
                evaluacion__proyecto=proyecto,
                pregunta_id__in=preguntas_ids
            )
            
            if respuestas.exists():
                avg_valor = respuestas.aggregate(Avg('valor'))['valor__avg']
                max_posible = 3.0  # Valor máximo por pregunta
                porcentaje = (avg_valor / max_posible) * 100 if avg_valor else 0
                
                caracteristicas_stats.append({
                    'caracteristica': caracteristica.nombre,
                    'codigo': caracteristica.codigo,
                    'promedio_valor': round(avg_valor, 2) if avg_valor else 0,
                    'porcentaje_cumplimiento': round(porcentaje, 2),
                    'num_preguntas_respondidas': respuestas.count()
                })
        
        return Response({
            'proyecto': proyecto.nombre,
            'num_evaluaciones': num_evaluaciones,
            'evaluaciones_completadas': evaluaciones_completadas,
            'caracteristicas': caracteristicas_stats
        })


class EvaluacionViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar Evaluaciones de software.
    """
    serializer_class = EvaluacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['proyecto', 'estado', 'evaluador']
    search_fields = ['proyecto__nombre']
    ordering_fields = ['fecha_creacion', 'estado']

    def get_queryset(self):
        """
        Filtra para que los usuarios solo vean las evaluaciones de sus proyectos
        o las que ellos mismos realizaron, excepto los superusuarios.
        """
        if self.request.user.is_superuser:
            return Evaluacion.objects.all()
        return Evaluacion.objects.filter(
            Q(proyecto__propietario=self.request.user) | 
            Q(evaluador=self.request.user)
        )
    
    def perform_create(self, serializer):
        # Establece automáticamente al usuario actual como evaluador
        serializer.save(evaluador=self.request.user)
    
    @action(detail=True, methods=['get'])
    def resultados(self, request, pk=None):
        """
        Obtiene resultados detallados de la evaluación agrupados por característica.
        """
        evaluacion = self.get_object()
        
        # Estructura para agrupar resultados
        resultados = []
        
        # Para cada característica
        for caracteristica in Caracteristica.objects.all():
            caract_data = {
                'caracteristica': {
                    'id': caracteristica.id,
                    'nombre': caracteristica.nombre,
                    'codigo': caracteristica.codigo,
                    'descripcion': caracteristica.descripcion
                },
                'subcaracteristicas': [],
                'porcentaje_cumplimiento': 0,
                'nivel_cumplimiento': 0
            }
            
            total_valor = 0
            total_preguntas = 0
            
            # Para cada subcaracterística de esta característica
            for subcaract in caracteristica.subcaracteristicas.all():
                subcaract_data = {
                    'id': subcaract.id,
                    'nombre': subcaract.nombre,
                    'codigo': subcaract.codigo,
                    'preguntas': []
                }
                
                # Para cada pregunta de esta subcaracterística
                for pregunta in subcaract.preguntas.all():
                    try:
                        respuesta = RespuestaPregunta.objects.get(
                            evaluacion=evaluacion,
                            pregunta=pregunta
                        )
                        
                        # Suma para cálculos
                        total_valor += respuesta.valor
                        total_preguntas += 1
                        
                        subcaract_data['preguntas'].append({
                            'id': pregunta.id,
                            'codigo': pregunta.codigo,
                            'texto': pregunta.texto,
                            'respuesta': {
                                'id': respuesta.id,
                                'valor': respuesta.valor,
                                'observacion': respuesta.observacion,
                                'tiene_evidencia': bool(respuesta.evidencia),
                                'evidencia_url': request.build_absolute_uri(respuesta.evidencia.url) if respuesta.evidencia else None
                            }
                        })
                    except RespuestaPregunta.DoesNotExist:
                        # Pregunta no respondida
                        subcaract_data['preguntas'].append({
                            'id': pregunta.id,
                            'codigo': pregunta.codigo,
                            'texto': pregunta.texto,
                            'respuesta': None
                        })
                
                caract_data['subcaracteristicas'].append(subcaract_data)
            
            # Cálculo de porcentaje para esta característica
            if total_preguntas > 0:
                porcentaje = (total_valor * 100) / (total_preguntas * 3)
                caract_data['porcentaje_cumplimiento'] = round(porcentaje, 2)
                
                # Determinar nivel de cumplimiento
                if porcentaje <= 30:
                    caract_data['nivel_cumplimiento'] = 0
                elif porcentaje <= 50:
                    caract_data['nivel_cumplimiento'] = 1
                elif porcentaje <= 89:
                    caract_data['nivel_cumplimiento'] = 2
                else:
                    caract_data['nivel_cumplimiento'] = 3
            
            resultados.append(caract_data)
        
        return Response({
            'evaluacion_id': evaluacion.id,
            'proyecto': evaluacion.proyecto.nombre,
            'estado': evaluacion.estado,
            'fecha_creacion': evaluacion.fecha_creacion,
            'fecha_actualizacion': evaluacion.fecha_actualizacion,
            'porcentaje_total': evaluacion.calcular_porcentaje_total(),
            'nivel_cumplimiento': evaluacion.obtener_nivel_cumplimiento(),
            'resultados': resultados
        })
    
    @action(detail=True, methods=['post'])
    def completar(self, request, pk=None):
        """
        Marca una evaluación como completada si todas las preguntas relevantes han sido respondidas.
        """
        evaluacion = self.get_object()
        
        # Verificar si el usuario tiene permiso
        if not request.user.is_superuser and request.user != evaluacion.evaluador:
            return Response({'error': 'No tiene permiso para completar esta evaluación'}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        # Verificar si ya está completada
        if evaluacion.estado == 'completada':
            return Response({'message': 'La evaluación ya está marcada como completada'})
        
        # Contar preguntas respondidas
        todas_preguntas = Pregunta.objects.all().count()
        respondidas = RespuestaPregunta.objects.filter(evaluacion=evaluacion).count()
        
        # Verificar si hay suficientes respuestas
        if respondidas < todas_preguntas * 0.8:  # Al menos 80% de preguntas respondidas
            return Response({
                'error': 'Debe responder al menos el 80% de las preguntas para completar la evaluación',
                'respondidas': respondidas,
                'total': todas_preguntas,
                'porcentaje': round((respondidas / todas_preguntas) * 100, 2)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Actualizar estado
        evaluacion.estado = 'completada'
        evaluacion.save()
        
        return Response({
            'message': 'Evaluación marcada como completada exitosamente',
            'porcentaje_cumplimiento': evaluacion.calcular_porcentaje_total(),
            'nivel_cumplimiento': evaluacion.obtener_nivel_cumplimiento()
        })


class RespuestaPreguntaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar Respuestas a las preguntas de evaluación.
    """
    serializer_class = RespuestaPreguntaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['evaluacion', 'pregunta', 'valor']

    def get_queryset(self):
        """
        Filtra para que los usuarios solo vean respuestas relacionadas con sus evaluaciones
        o proyectos, excepto los superusuarios.
        """
        if self.request.user.is_superuser:
            return RespuestaPregunta.objects.all()
        
        return RespuestaPregunta.objects.filter(
            Q(evaluacion__evaluador=self.request.user) | 
            Q(evaluacion__proyecto__propietario=self.request.user)
        )
    
    def create(self, request, *args, **kwargs):
        # Añadir validaciones específicas
        evaluacion_id = request.data.get('evaluacion')
        if evaluacion_id:
            evaluacion = get_object_or_404(Evaluacion, pk=evaluacion_id)
            
            # No permitir modificar evaluaciones completadas
            if evaluacion.estado == 'completada':
                return Response(
                    {'error': 'No se pueden añadir respuestas a una evaluación completada'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar si el usuario tiene permiso para esta evaluación
            if not request.user.is_superuser and request.user != evaluacion.evaluador:
                return Response(
                    {'error': 'No tiene permiso para añadir respuestas a esta evaluación'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Continuar con el proceso de creación estándar
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        # Añadir validaciones similares para actualización
        instance = self.get_object()
        
        # No permitir modificar evaluaciones completadas
        if instance.evaluacion.estado == 'completada':
            return Response(
                {'error': 'No se pueden modificar respuestas de una evaluación completada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar si el usuario tiene permiso
        if not request.user.is_superuser and request.user != instance.evaluacion.evaluador:
            return Response(
                {'error': 'No tiene permiso para modificar esta respuesta'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Continuar con el proceso de actualización estándar
        return super().update(request, *args, **kwargs)