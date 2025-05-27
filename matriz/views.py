# matriz/views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.db import transaction
from rest_framework.permissions import AllowAny  # Agregar este import


from .models import MatrizRiesgo, RiesgoMatriz, CausaRiesgo, ParametroMatriz, AuditoriaMatriz
from .serializers import (
    MatrizRiesgoSerializer, 
    MatrizRiesgoListSerializer,
    MatrizRiesgoFrontendSerializer,
    RiesgoMatrizSerializer, 
    CausaRiesgoSerializer,
    ParametroMatrizSerializer,
    AuditoriaMatrizSerializer
)
from .permissions import MatrizRiesgoPermission

class MatrizRiesgoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar matrices de riesgo
    """
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['responsable', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion', 'responsable']
    ordering_fields = ['fecha_creacion', 'fecha_modificacion', 'nombre']
    ordering = ['-fecha_modificacion']
    
    def get_queryset(self):
        """Filtrar matrices según el usuario"""
        user = self.request.user
        queryset = MatrizRiesgo.objects.select_related('creado_por', 'empresa')
        
        # Administradores ven todas las matrices
        if user.groups.filter(name='Administradores').exists():
            return queryset
        
        # Usuarios normales solo ven las de su empresa
        if hasattr(user, 'empresa') and user.empresa:
            return queryset.filter(empresa=user.empresa)
        
        return queryset.none()
    
    def get_serializer_class(self):
        """Usar diferentes serializers según la acción"""
        if self.action == 'list':
            return MatrizRiesgoListSerializer
        elif self.action in ['create_frontend', 'update_frontend']:
            return MatrizRiesgoFrontendSerializer
        return MatrizRiesgoSerializer
    
    def perform_create(self, serializer):
        """Asignar usuario y empresa al crear"""
        user = self.request.user
        if not hasattr(user, 'empresa') or not user.empresa:
            raise serializers.ValidationError("El usuario no tiene una empresa asignada.")
        
        matriz = serializer.save(creado_por=user, empresa=user.empresa)
        
        # Registrar auditoría
        AuditoriaMatriz.objects.create(
            matriz=matriz,
            usuario=user,
            accion='CREATE',
            descripcion=f'Matriz creada: {matriz.nombre}',
            datos_nuevos=serializer.data
        )
    
    def perform_update(self, serializer):
        """Registrar cambios en auditoría"""
        datos_anteriores = MatrizRiesgoSerializer(self.get_object()).data
        matriz = serializer.save()
        
        AuditoriaMatriz.objects.create(
            matriz=matriz,
            usuario=self.request.user,
            accion='UPDATE',
            descripcion=f'Matriz actualizada: {matriz.nombre}',
            datos_anteriores=datos_anteriores,
            datos_nuevos=serializer.data
        )
    
    def perform_destroy(self, instance):
        """Registrar eliminación en auditoría"""
        AuditoriaMatriz.objects.create(
            matriz=instance,
            usuario=self.request.user,
            accion='DELETE',
            descripcion=f'Matriz eliminada: {instance.nombre}',
            datos_anteriores=MatrizRiesgoSerializer(instance).data
        )
        instance.delete()
    
    @action(detail=False, methods=['post'])
    def create_frontend(self, request):
        """
        Endpoint especial para crear matrices desde el frontend
        Maneja la estructura específica del componente React
        """
        serializer = MatrizRiesgoFrontendSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                matriz = serializer.save()
                return Response(
                    {
                        'message': 'Matriz creada exitosamente',
                        'matriz': MatrizRiesgoSerializer(matriz, context={'request': request}).data
                    },
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {'error': f'Error al crear la matriz: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(
            {'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['put'])
    def update_frontend(self, request, pk=None):
        """
        Endpoint especial para actualizar matrices desde el frontend
        """
        matriz = self.get_object()
        serializer = MatrizRiesgoFrontendSerializer(
            matriz,
            data=request.data,
            context={'request': request},
            partial=True
        )
        
        if serializer.is_valid():
            try:
                matriz = serializer.save()
                return Response(
                    {
                        'message': 'Matriz actualizada exitosamente',
                        'matriz': MatrizRiesgoSerializer(matriz, context={'request': request}).data
                    },
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(
                    {'error': f'Error al actualizar la matriz: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(
            {'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['get'])
    def estadisticas(self, request, pk=None):
        """Obtener estadísticas detalladas de una matriz"""
        matriz = self.get_object()
        riesgos = matriz.riesgos.all()
        
        estadisticas = {
            'total_riesgos': riesgos.count(),
            'riesgos_por_tipo': {},
            'riesgos_por_nivel': matriz.resumen_riesgos_por_nivel,
            'riesgos_aceptados': riesgos.filter(aceptado=True).count(),
            'riesgos_no_aceptados': riesgos.filter(aceptado=False).count(),
            'promedio_probabilidad': 0,
            'promedio_impacto': 0,
            'efectividad_promedio_controles': 0
        }
        
        if riesgos.exists():
            # Estadísticas por tipo
            for tipo, _ in RiesgoMatriz.TIPOS_RIESGO:
                count = riesgos.filter(tipo_riesgo=tipo).count()
                if count > 0:
                    estadisticas['riesgos_por_tipo'][tipo] = count
            
            # Promedios
            from django.db.models import Avg
            promedios = riesgos.aggregate(
                Avg('probabilidad'),
                Avg('impacto'),
                Avg('efectividad_control')
            )
            
            estadisticas['promedio_probabilidad'] = round(promedios['probabilidad__avg'] or 0, 2)
            estadisticas['promedio_impacto'] = round(promedios['impacto__avg'] or 0, 2)
            estadisticas['efectividad_promedio_controles'] = round(promedios['efectividad_control__avg'] or 0, 2)
        
        return Response(estadisticas)
    
    @action(detail=True, methods=['get'])
    def exportar(self, request, pk=None):
        """Exportar matriz en formato JSON para respaldo"""
        matriz = self.get_object()
        serializer = MatrizRiesgoSerializer(matriz)
        
        return Response({
            'matriz': serializer.data,
            'fecha_exportacion': timezone.now(),
            'exportado_por': request.user.get_full_name()
        })
    
    @action(detail=False, methods=['get'])
    def mis_matrices(self, request):
        """Obtener matrices del usuario actual"""
        user = request.user
        
        if hasattr(user, 'empresa') and user.empresa:
            queryset = self.get_queryset().filter(empresa=user.empresa)
        else:
            queryset = MatrizRiesgo.objects.none()
        
        # Aplicar filtros de búsqueda si existen
        search = request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) | 
                Q(descripcion__icontains=search) |
                Q(responsable__icontains=search)
            )
        
        # Aplicar filtro de nivel de riesgo
        filter_risk_level = request.query_params.get('filterRiskLevel', '')
        if filter_risk_level:
            # Filtrar matrices que contengan riesgos del nivel especificado
            matrices_con_nivel = []
            for matriz in queryset:
                if any(r.calcular_zona_riesgo()['nivel'] == filter_risk_level.replace('_', ' ') 
                       for r in matriz.riesgos.all()):
                    matrices_con_nivel.append(matriz.id)
            queryset = queryset.filter(id__in=matrices_con_nivel)
        
        serializer = MatrizRiesgoListSerializer(queryset, many=True)
        return Response({
            'matrices': serializer.data,
            'total': queryset.count(),
            'empresa': user.empresa.nombre if hasattr(user, 'empresa') and user.empresa else None
        })


class RiesgoMatrizViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar riesgos individuales
    """
    serializer_class = RiesgoMatrizSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['matriz', 'tipo_riesgo', 'probabilidad', 'impacto', 'aceptado']
    search_fields = ['nombre', 'descripcion', 'codigo']
    
    def get_queryset(self):
        """Filtrar riesgos según la empresa del usuario"""
        user = self.request.user
        
        if user.groups.filter(name='Administradores').exists():
            return RiesgoMatriz.objects.all()
        
        if hasattr(user, 'empresa') and user.empresa:
            return RiesgoMatriz.objects.filter(matriz__empresa=user.empresa)
        
        return RiesgoMatriz.objects.none()
    
    def get_serializer_context(self):
        """Agregar matriz_id al contexto para validaciones"""
        context = super().get_serializer_context()
        if 'matriz_pk' in self.kwargs:
            context['matriz_id'] = self.kwargs['matriz_pk']
        return context


class ParametroMatrizViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para obtener parámetros del sistema (solo lectura)
    """
    queryset = ParametroMatriz.objects.filter(activo=True)
    serializer_class = ParametroMatrizSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tipo']


class ParametrosConfiguracionView(APIView):
    """
    Vista para obtener todos los parámetros de configuración del sistema
    """
    permission_classes = [AllowAny]  # ← CAMBIAR AQUÍ: Permitir acceso sin autenticación
    
    def get(self, request):
        """Obtener parámetros hardcodeados"""
        parametros = {
            'probabilidad': [
                {'value': 1, 'label': 'Raro', 'description': 'Muy improbable que ocurra'},
                {'value': 2, 'label': 'Improbable', 'description': 'Poco probable que ocurra'},
                {'value': 3, 'label': 'Posible', 'description': 'Podría ocurrir'},
                {'value': 4, 'label': 'Probable', 'description': 'Probablemente ocurrirá'},
                {'value': 5, 'label': 'Casi Seguro', 'description': 'Casi seguro que ocurrirá'}
            ],
            'impacto': [
                {'value': 1, 'label': 'Insignificante', 'description': 'No hay interrupción en las operaciones'},
                {'value': 2, 'label': 'Menor', 'description': 'Interrupción por algunas horas'},
                {'value': 3, 'label': 'Moderado', 'description': 'Interrupción por un día'},
                {'value': 4, 'label': 'Mayor', 'description': 'Interrupción por más de dos días'},
                {'value': 5, 'label': 'Catastrófico', 'description': 'Interrupción por más de cinco días'}
            ],
            'tipos_riesgo': [
                {'value': 'Operativo', 'label': 'Operativo'},
                {'value': 'Estratégico', 'label': 'Estratégico'},
                {'value': 'Financiero', 'label': 'Financiero'},
                {'value': 'Cumplimiento', 'label': 'Cumplimiento'},
                {'value': 'Tecnológico', 'label': 'Tecnológico'}
            ],
            'tipos_control': [
                {'value': 'Preventivo', 'label': 'Preventivo'},
                {'value': 'Correctivo', 'label': 'Correctivo'},
                {'value': 'Detectivo', 'label': 'Detectivo'}
            ],
            'factores_causa': [
                {'value': 'Información', 'label': 'Información'},
                {'value': 'Método', 'label': 'Método'},
                {'value': 'Personas', 'label': 'Personas'},
                {'value': 'Sistemas de información', 'label': 'Sistemas de información'},
                {'value': 'Infraestructura', 'label': 'Infraestructura'}
            ]
        }
        
        return Response(parametros)

class EstadisticasEmpresaMatricesView(APIView):
    """
    Vista para obtener estadísticas de matrices de la empresa
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Estadísticas generales de matrices de riesgo de la empresa"""
        user = request.user
        
        if not hasattr(user, 'empresa') or not user.empresa:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        matrices = MatrizRiesgo.objects.filter(empresa=user.empresa)
        riesgos = RiesgoMatriz.objects.filter(matriz__empresa=user.empresa)
        
        estadisticas = {
            'total_matrices': matrices.count(),
            'total_riesgos': riesgos.count(),
            'riesgos_por_nivel': {
                'EXTREMA': 0, 'ALTA': 0, 'MODERADA': 0, 'BAJA': 0, 'MUY_BAJA': 0
            },
            'riesgos_por_tipo': {},
            'matrices_recientes': [],
            'riesgos_criticos': [],
            'efectividad_promedio_controles': 0,
            'porcentaje_riesgos_aceptados': 0
        }
        
        # Calcular riesgos por nivel
        for riesgo in riesgos:
            zona = riesgo.calcular_zona_riesgo()
            nivel_key = zona['nivel'].replace(' ', '_')
            if nivel_key in estadisticas['riesgos_por_nivel']:
                estadisticas['riesgos_por_nivel'][nivel_key] += 1
        
        # Riesgos por tipo
        for tipo, _ in RiesgoMatriz.TIPOS_RIESGO:
            count = riesgos.filter(tipo_riesgo=tipo).count()
            if count > 0:
                estadisticas['riesgos_por_tipo'][tipo] = count
        
        # Matrices recientes (últimas 5)
        matrices_recientes = matrices.order_by('-fecha_modificacion')[:5]
        estadisticas['matrices_recientes'] = [
            {
                'id': m.id,
                'nombre': m.nombre,
                'fecha_modificacion': m.fecha_modificacion,
                'total_riesgos': m.total_riesgos,
                'responsable': m.responsable
            }
            for m in matrices_recientes
        ]
        
        # Riesgos críticos (nivel EXTREMA y ALTA)
        riesgos_criticos = [
            r for r in riesgos 
            if r.calcular_zona_riesgo()['nivel'] in ['EXTREMA', 'ALTA']
        ][:10]
        
        estadisticas['riesgos_criticos'] = [
            {
                'id': r.id,
                'nombre': r.nombre,
                'matriz': r.matriz.nombre,
                'zona_riesgo': r.calcular_zona_riesgo(),
                'aceptado': r.aceptado
            }
            for r in riesgos_criticos
        ]
        
        # Calcular promedios
        if riesgos.exists():
            from django.db.models import Avg
            efectividad_avg = riesgos.aggregate(Avg('efectividad_control'))['efectividad_control__avg']
            estadisticas['efectividad_promedio_controles'] = round(efectividad_avg or 0, 2)
            
            riesgos_aceptados = riesgos.filter(aceptado=True).count()
            estadisticas['porcentaje_riesgos_aceptados'] = round(
                (riesgos_aceptados / riesgos.count()) * 100, 2
            )
        
        return Response(estadisticas)


class AuditoriaMatrizViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar auditoría de matrices (solo lectura)
    """
    serializer_class = AuditoriaMatrizSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['matriz', 'usuario', 'accion']
    ordering = ['-fecha_accion']
    
    def get_queryset(self):
        """Filtrar auditoría según permisos del usuario"""
        user = self.request.user
        
        if user.groups.filter(name='Administradores').exists():
            return AuditoriaMatriz.objects.all()
        
        if hasattr(user, 'empresa') and user.empresa:
            return AuditoriaMatriz.objects.filter(matriz__empresa=user.empresa)
        
        return AuditoriaMatriz.objects.none()