from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'caracteristicas', views.CaracteristicaViewSet, basename='caracteristica')
router.register(r'subcaracteristicas', views.SubcaracteristicaViewSet, basename='subcaracteristica')
router.register(r'preguntas', views.PreguntaViewSet, basename='pregunta')
router.register(r'proyectos', views.ProyectoViewSet, basename='proyecto')
router.register(r'evaluaciones', views.EvaluacionViewSet, basename='evaluacion')
router.register(r'respuestas', views.RespuestaPreguntaViewSet, basename='respuesta')

urlpatterns = [
    path('', include(router.urls)),
]