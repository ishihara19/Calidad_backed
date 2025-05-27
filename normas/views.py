from rest_framework import serializers  # Para ValidationError en perform_create
from rest_framework import viewsets
from .models import Norma, Caracteristica, SubCaracteristica, CalificacionSubCaracteristica
from .serializers import NormaSerializer, CaracteristicaSerializer, SubCaracteristicaSerializer, CalificacionSubCaracteristicaSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from empresa.models import Empresa
from API_C.utils import generar_codigo_evaluacion
from django.db import transaction
from .permissions import IsAdminOrReadOnly  # ✅ nuevo import
from rest_framework.permissions import IsAuthenticated  # ✅ AGREGADO: Import faltante
from rest_framework.decorators import action
from .permissions import CanManageNorma

class NormaViewSet(viewsets.ModelViewSet):
    queryset = Norma.objects.all()
    serializer_class = NormaSerializer
    permission_classes = [IsAdminOrReadOnly]  # ✅ nuevo control de acceso
    permission_classes = [IsAuthenticated, CanManageNorma]

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        norma = self.get_object()
        norma.estado = 'aprobada'
        norma.save()
        return Response({'status': 'norma aprobada'})

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        norma = self.get_object()
        norma.estado = 'revision'
        norma.save()
        return Response({'status': 'norma en revisión'})

class CaracteristicaViewSet(viewsets.ModelViewSet):
    queryset = Caracteristica.objects.all()
    serializer_class = CaracteristicaSerializer
    permission_classes = [IsAdminOrReadOnly]

class SubCaracteristicaViewSet(viewsets.ModelViewSet):
    queryset = SubCaracteristica.objects.all()
    serializer_class = SubCaracteristicaSerializer
    permission_classes = [IsAdminOrReadOnly]

class CalificacionSubCaracteristicaViewSet(viewsets.ModelViewSet):
    queryset = CalificacionSubCaracteristica.objects.all()
    serializer_class = CalificacionSubCaracteristicaSerializer
    permission_classes = [IsAuthenticated]  # solo usuarios autenticados pueden calificar
    
    def perform_create(self, serializer):
        usuario = self.request.user
        # ✅ MEJORADO: Validar que el usuario tenga empresa asignada
        if not hasattr(usuario, 'empresa') or not usuario.empresa:
            raise serializers.ValidationError("El usuario no tiene una empresa asignada.")
        
        empresa = usuario.empresa 
        codigo_empresa = empresa.codigo_empresa
        serializer.save(usuario=usuario, empresa=empresa, codigo_empresa=codigo_empresa)
        
class CalificacionesBatchView(APIView):
    permission_classes = [IsAuthenticated] # ¡Importante para la seguridad!

    def post(self, request):
        usuario = request.user
        empresa_id = request.data.get('empresa')  # ✅ RENOMBRADO: Más claro
        
        # ✅ MEJORADO: Validación inicial de empresa_id
        if not empresa_id:
            return Response(
                {"error": "El campo 'empresa' es requerido."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ✅ MEJORADO: Manejo de empresa
        try:
            empresa_obj = Empresa.objects.get(id=empresa_id)
        except Empresa.DoesNotExist:
            return Response(
                {"error": "Empresa no encontrada"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:  # ✅ AGREGADO: Por si empresa_id no es un número válido
            return Response(
                {"error": "El ID de empresa debe ser un número válido."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        empresa_actual = empresa_obj
        print(f"Empresa actual: {empresa_actual}")  # ✅ MEJORADO: f-string más legible

        # Validar que el usuario y la empresa tengan los campos necesarios para generar el código
        if not hasattr(usuario, 'document') or not usuario.document:
            return Response(
                {"error": "Falta el documento del usuario para generar el código de evaluación."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        if not hasattr(empresa_actual, 'codigo_empresa') or not empresa_actual.codigo_empresa:
            return Response(
                {"error": "Falta el código de la empresa para generar el código de evaluación."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        calificaciones_data = request.data.get("calificaciones", [])
        print(f"Calificaciones data: {calificaciones_data}")  # ✅ MEJORADO: f-string
        
        if not isinstance(calificaciones_data, list) or not calificaciones_data:
            return Response(
                {"error": "Se esperaba una lista no vacía de 'calificaciones'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ MEJORADO: Generación del código con mejor manejo de errores
        try:
            codigo_evaluacion_lote = generar_codigo_evaluacion(
                CalificacionSubCaracteristica,
                empresa_actual.codigo_empresa,
                usuario.document
            )
        except Exception as e:  # ✅ AGREGADO: Captura errores de la función
            return Response(
                {"error": f"Error al generar el código de evaluación: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        if not codigo_evaluacion_lote:
            return Response(
                {"error": "No se pudo generar el código de evaluación para el lote."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # ✅ MEJORADO: Crear contexto más completo para el serializer
        serializer = CalificacionSubCaracteristicaSerializer(
            data=calificaciones_data, 
            many=True, 
            context={
                'request': request,
                'usuario': usuario,
                'empresa': empresa_actual
            }
        )

        if serializer.is_valid():
            calificaciones_para_crear = []
            
            # ✅ MEJORADO: Validación adicional antes de crear objetos
            for item_validado in serializer.validated_data:
                # Verificar que la subcaracterística existe
                if not item_validado.get('subcaracteristica'):
                    return Response(
                        {"error": "Todas las calificaciones deben tener una subcaracterística válida."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                calificaciones_para_crear.append(
                    CalificacionSubCaracteristica(
                        usuario=usuario,
                        empresa=empresa_actual,
                        subcaracteristica=item_validado['subcaracteristica'],
                        puntos=item_validado['puntos'],
                        observacion=item_validado.get('observacion', ""),
                        codigo_calificacion=codigo_evaluacion_lote
                    )
                )

            try:
                with transaction.atomic():
                    # ✅ MEJORADO: Usar bulk_create para mejor rendimiento
                    instancias_creadas = CalificacionSubCaracteristica.objects.bulk_create(
                        calificaciones_para_crear
                    )
                    
                    # ✅ NOTA: bulk_create no activa signals ni retorna IDs en algunas versiones
                    # Si necesitas los IDs o signals, usa el método original:
                    # instancias_creadas = []
                    # for calificacion_obj in calificaciones_para_crear:
                    #     calificacion_obj.save() 
                    #     instancias_creadas.append(calificacion_obj)
                    
                # ✅ MEJORADO: Si usas bulk_create, necesitas refrescar los datos
                if instancias_creadas:
                    # Obtener las instancias recién creadas para serializar
                    instancias_recientes = CalificacionSubCaracteristica.objects.filter(
                        codigo_calificacion=codigo_evaluacion_lote,
                        usuario=usuario,
                        empresa=empresa_actual
                    )
                    resultado_serializer = CalificacionSubCaracteristicaSerializer(
                        instancias_recientes, 
                        many=True
                    )
                else:
                    # ✅ AGREGADO: Caso cuando bulk_create no funciona como esperado
                    resultado_serializer = CalificacionSubCaracteristicaSerializer(
                        instancias_creadas, 
                        many=True
                    )
                
                return Response(
                    {
                        "message": "Calificaciones creadas exitosamente",
                        "codigo_evaluacion": codigo_evaluacion_lote,
                        "calificaciones": resultado_serializer.data
                    }, 
                    status=status.HTTP_201_CREATED
                )
            
            except Exception as e: 
                return Response(
                    {"error": f"Ocurrió un error al guardar las calificaciones en la base de datos: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            # ✅ MEJORADO: Respuesta de error más detallada
            return Response(
                {
                    "error": "Datos de calificaciones inválidos",
                    "detalles": serializer.errors
                }, 
                status=status.HTTP_400_BAD_REQUEST
            )