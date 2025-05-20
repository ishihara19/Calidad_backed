from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NormaViewSet, CaracteristicaViewSet, SubCaracteristicaViewSet, CalificacionSubCaracteristicaViewSet,CalificacionesBatchView

router = DefaultRouter()
router.register(r'normas', NormaViewSet)
router.register(r'caracteristicas', CaracteristicaViewSet)
router.register(r'subcaracteristicas', SubCaracteristicaViewSet)
router.register(r'preguntas', CalificacionSubCaracteristicaViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('listar-normas',NormaViewSet.as_view({'get':'list'})),
    path('listar-norma/<pk>',NormaViewSet.as_view({'get':'retrieve'})),
    path('listar-pregintas',CalificacionSubCaracteristicaViewSet.as_view({'get':'list'})),
    path('crear-pregunta',CalificacionSubCaracteristicaViewSet.as_view({'post':'create'})),
    path('crear-mult-preguntas', CalificacionesBatchView.as_view())
]