from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NormaViewSet, CaracteristicaViewSet, SubCaracteristicaViewSet, NormasPlantillasView

router = DefaultRouter()
router.register(r'normas', NormaViewSet, basename='norma')
router.register(r'caracteristicas', CaracteristicaViewSet, basename='caracteristica')
router.register(r'subcaracteristicas', SubCaracteristicaViewSet, basename='subcaracteristica')

urlpatterns = [
    # Rutas del router (automáticas)
    path('', include(router.urls)),
    
    # Rutas específicas optimizadas
    path('plantillas/', NormasPlantillasView.as_view(), name='normas-plantillas'),
    
    # Endpoints de conveniencia (más claros para el frontend)
    path('normas-activas/', NormaViewSet.as_view({
        'get': 'list'
    }), {'estado': 'aprobada'}, name='normas-activas'),
    
    # Rutas específicas que evitan queries innecesarias
    path('normas/<int:pk>/plantilla/', NormaViewSet.as_view({
        'get': 'plantilla_evaluacion'
    }), name='norma-plantilla'),
    
    path('normas/<int:pk>/validar-porcentajes/', NormaViewSet.as_view({
        'post': 'validar_porcentajes'
    }), name='norma-validar-porcentajes'),
    
    path('normas/estadisticas/', NormaViewSet.as_view({
        'get': 'estadisticas'
    }), name='normas-estadisticas'),
    
    # Rutas para obtener solo subcaracterísticas
    path('caracteristicas/<int:pk>/subcaracteristicas/', CaracteristicaViewSet.as_view({
        'get': 'subcaracteristicas'
    }), name='caracteristica-subcaracteristicas'),
    
    # Filtros optimizados
    path('subcaracteristicas/por-caracteristica/<int:caracteristica_id>/', 
         SubCaracteristicaViewSet.as_view({'get': 'list'}), 
         name='subcaracteristicas-por-caracteristica'),
    
    path('subcaracteristicas/por-norma/<int:norma_id>/', 
         SubCaracteristicaViewSet.as_view({'get': 'list'}), 
         name='subcaracteristicas-por-norma'),
]