from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NormaViewSet, CaracteristicaViewSet, SubCaracteristicaViewSet, CalificacionSubCaracteristicaViewSet

router = DefaultRouter()
router.register(r'normas', NormaViewSet)
router.register(r'caracteristicas', CaracteristicaViewSet)
router.register(r'subcaracteristicas', SubCaracteristicaViewSet)
router.register(r'preguntas', CalificacionSubCaracteristicaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]