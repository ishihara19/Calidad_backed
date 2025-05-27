
# matriz/urls.py - Versión con drf-nested-routers
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views import (
    MatrizRiesgoViewSet,
    RiesgoMatrizViewSet,
    ParametroMatrizViewSet,
    AuditoriaMatrizViewSet,
    ParametrosConfiguracionView,
    EstadisticasEmpresaMatricesView
)

# Router principal
router = DefaultRouter()
router.register(r'matrices', MatrizRiesgoViewSet, basename='matriz')
router.register(r'parametros', ParametroMatrizViewSet, basename='parametro')
router.register(r'auditoria', AuditoriaMatrizViewSet, basename='auditoria')

# Router anidado para riesgos dentro de matrices
matrices_router = routers.NestedDefaultRouter(router, r'matrices', lookup='matriz')
matrices_router.register(r'riesgos', RiesgoMatrizViewSet, basename='matriz-riesgos')

urlpatterns = [
    # Rutas del router principal
    path('', include(router.urls)),
    
    # Rutas del router anidado
    path('', include(matrices_router.urls)),
    
    # ===== RUTAS ESPECÍFICAS PARA EL FRONTEND =====
    
    # Crear matriz con estructura del frontend
    path('matrices/create-frontend/', MatrizRiesgoViewSet.as_view({
        'post': 'create_frontend'
    }), name='crear-matriz-frontend'),
    
    # Actualizar matriz con estructura del frontend
    path('matrices/<str:pk>/update-frontend/', MatrizRiesgoViewSet.as_view({
        'put': 'update_frontend'
    }), name='actualizar-matriz-frontend'),
    
    # Mis matrices (filtradas por empresa)
    path('mis-matrices/', MatrizRiesgoViewSet.as_view({
        'get': 'mis_matrices'
    }), name='mis-matrices'),
    
    # Estadísticas de una matriz específica
    path('matrices/<str:pk>/estadisticas/', MatrizRiesgoViewSet.as_view({
        'get': 'estadisticas'
    }), name='estadisticas-matriz'),
    
    # Exportar matriz
    path('matrices/<str:pk>/exportar/', MatrizRiesgoViewSet.as_view({
        'get': 'exportar'
    }), name='exportar-matriz'),
    
    # ===== RUTAS DE CONFIGURACIÓN Y UTILIDADES =====
    
    # Obtener todos los parámetros de configuración
    path('parametros-configuracion/', ParametrosConfiguracionView.as_view(), 
         name='parametros-configuracion'),
    
    # Estadísticas generales de la empresa
    path('estadisticas-empresa/', EstadisticasEmpresaMatricesView.as_view(), 
         name='estadisticas-empresa-matrices'),
]