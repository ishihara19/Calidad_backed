from rest_framework import viewsets
from .models import Norma, Caracteristica, SubCaracteristica, CalificacionSubCaracteristica
from .serializers import NormaSerializer, CaracteristicaSerializer, SubCaracteristicaSerializer, CalificacionSubCaracteristicaSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from empresa.models import Empresa
from API_C.utils import generar_codigo_evaluacion
from django.db import transaction

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
    
    def perform_create(self, serializer):
        usuario = self.request.user
        empresa = usuario.empresa 
        codigo_empresa = empresa.codigo_empresa
        serializer.save(usuario=usuario, empresa=empresa,codigo_empresa=codigo_empresa)
        
class CalificacionesBatchView(APIView):
    # permission_classes = [IsAuthenticated] # ¡Importante para la seguridad!

    def post(self, request):
        usuario = request.user
        empresa = request.data.get('empresa')
        
        
        if empresa: # Si se proporcionó un código de empresa
                try:
                    empresa_obj = Empresa.objects.get(id=empresa)
                except Empresa.DoesNotExist:
                    return Response({"erro":"Empresa no encontrada"}, status=status.HTTP_404_NOT_FOUND)
            
        empresa_actual = empresa_obj
        print(empresa_actual)
        
                
            

        # Validar que el usuario y la empresa tengan los campos necesarios para generar el código
        if not hasattr(usuario, 'document') or not usuario.document:
             return Response({"error": "Falta el documento del usuario para generar el código de evaluación."}, status=status.HTTP_400_BAD_REQUEST)
        if not hasattr(empresa_actual, 'codigo_empresa') or not empresa_actual.codigo_empresa:
             return Response({"error": "Falta el código de la empresa para generar el código de evaluación."}, status=status.HTTP_400_BAD_REQUEST)


        calificaciones_data = request.data.get("calificaciones", [])
        print(calificaciones_data)
        if not isinstance(calificaciones_data, list) or not calificaciones_data:
            return Response(
                {"error": "Se esperaba una lista no vacía de 'calificaciones'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        
        codigo_evaluacion_lote = generar_codigo_evaluacion(
            CalificacionSubCaracteristica, # Pasando la clase como en tu modelo
            empresa_actual.codigo_empresa,
            usuario.document
        )
        if not codigo_evaluacion_lote: # Verificar que el código se generó
             return Response({"error": "No se pudo generar el código de evaluación para el lote."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        
        serializer = CalificacionSubCaracteristicaSerializer(data=calificaciones_data, many=True, context={'request': request})

        if serializer.is_valid():
            calificaciones_para_crear = []
            for item_validado in serializer.validated_data:
                # item_validado contiene:
                # - subcaracteristica (instancia del modelo SubCaracteristica)
                # - puntos
                # - observacion (si se proveyó)
                calificaciones_para_crear.append(
                    CalificacionSubCaracteristica(
                        usuario=usuario,
                        empresa=empresa_actual,
                        subcaracteristica=item_validado['subcaracteristica'], # Correcto: usar la instancia validada
                        puntos=item_validado['puntos'],
                        observacion=item_validado.get('observacion', ""), # .get() para opcional
                        codigo_calificacion=codigo_evaluacion_lote  # ¡Asignar el código del lote!
                    )
                )

            try:
                with transaction.atomic():
                    instancias_creadas = []
                    for calificacion_obj in calificaciones_para_crear:
                        calificacion_obj.save() 
                        instancias_creadas.append(calificacion_obj)                    
                    
                resultado_serializer = CalificacionSubCaracteristicaSerializer(instancias_creadas, many=True)
                return Response(resultado_serializer.data, status=status.HTTP_201_CREATED)
            
            except Exception as e: 
                return Response(
                    {"error": f"Ocurrió un error al guardar las calificaciones en la base de datos: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)