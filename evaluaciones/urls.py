from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EvaluacionViewSet,
    CalificacionCaracteristicaViewSet,
    CalificacionSubCaracteristicaViewSet,
    EvaluacionFlexibleView,  # NUEVO
    NormaParaEvaluacionView,  # NUEVO
    ValidarPorcentajesView,   # NUEVO
    MisSoftwaresView,
    NormasDisponiblesView,    # NUEVO
    EstadisticasEmpresaView
)

router = DefaultRouter()
router.register(r'evaluaciones', EvaluacionViewSet, basename='evaluacion')
router.register(r'calificaciones-caracteristica', CalificacionCaracteristicaViewSet, basename='calificacion-caracteristica')
router.register(r'calificaciones-subcaracteristica', CalificacionSubCaracteristicaViewSet, basename='calificacion-subcaracteristica')

urlpatterns = [
    # Rutas del router
    path('', include(router.urls)),
    
    # ===== NUEVAS RUTAS PARA EL FLUJO DEL FRONTEND =====
    
    # Crear evaluación con el nuevo flujo flexible
    path('crear-evaluacion/', EvaluacionFlexibleView.as_view(), name='crear-evaluacion-flexible'),
    
    # Obtener estructura de norma para evaluación
    path('norma/<int:norma_id>/estructura/', NormaParaEvaluacionView.as_view(), name='norma-estructura'),
    
    # Validar porcentajes antes de enviar
    path('validar-porcentajes/', ValidarPorcentajesView.as_view(), name='validar-porcentajes'),
    
    # Obtener normas disponibles para evaluación
    path('normas-disponibles/', NormasDisponiblesView.as_view(), name='normas-disponibles'),
    
    # ===== RUTAS EXISTENTES MANTENIDAS =====
    
    # Rutas de conveniencia 
    path('mis-softwares/', MisSoftwaresView.as_view(), name='mis-softwares'),
    path('estadisticas-empresa/', EstadisticasEmpresaView.as_view(), name='estadisticas-empresa'),
    
    # Endpoints específicos de evaluaciones
    path('evaluaciones/mis-evaluaciones/', EvaluacionViewSet.as_view({'get': 'list'}), name='mis-evaluaciones'),
    path('evaluaciones/<int:pk>/completar/', EvaluacionViewSet.as_view({'post': 'completar'}), name='completar-evaluacion'),
    path('evaluaciones/<int:pk>/reporte/', EvaluacionViewSet.as_view({'get': 'reporte'}), name='reporte-evaluacion'),
]