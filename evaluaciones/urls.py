from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EvaluacionViewSet,
    CalificacionCaracteristicaViewSet,
    CalificacionSubCaracteristicaViewSet,
    EvaluacionCompletaView,
    MisSoftwaresView,
    EstadisticasEmpresaView
)

router = DefaultRouter()
router.register(r'evaluaciones', EvaluacionViewSet, basename='evaluacion')
router.register(r'calificaciones-caracteristica', CalificacionCaracteristicaViewSet, basename='calificacion-caracteristica')
router.register(r'calificaciones-subcaracteristica', CalificacionSubCaracteristicaViewSet, basename='calificacion-subcaracteristica')

urlpatterns = [
    # Rutas del router
    path('', include(router.urls)),
    
    # Rutas personalizadas
    path('crear-evaluacion-completa/', EvaluacionCompletaView.as_view(), name='crear-evaluacion-completa'),
    path('mis-softwares/', MisSoftwaresView.as_view(), name='mis-softwares'),
    path('estadisticas-empresa/', EstadisticasEmpresaView.as_view(), name='estadisticas-empresa'),
    
    # Rutas de conveniencia para endpoints específicos
    path('evaluaciones/mis-evaluaciones/', EvaluacionViewSet.as_view({'get': 'list'}), name='mis-evaluaciones'),
    path('evaluaciones/<int:pk>/completar/', EvaluacionViewSet.as_view({'post': 'completar'}), name='completar-evaluacion'),
    path('evaluaciones/<int:pk>/reporte/', EvaluacionViewSet.as_view({'get': 'reporte'}), name='reporte-evaluacion'),
]