from django.urls import path
from .authentication import LoginView, LogoutView
from .views import CustomUserCreateView, DocumentTypeListView, PersonTypeListView
urlpatterns = [
    path('login', LoginView.as_view(), name='login'), # inicio de sesión
    path('logout', LogoutView.as_view(), name='logout'),# cierre de sesión
    path('register', CustomUserCreateView.as_view(), name='user-register'),# registro de usuarios   
    path('list-document-type',DocumentTypeListView.as_view(), name='listed-document-type'),# listar tipo de documentos
    path('list-person-type',PersonTypeListView.as_view(),name='listed-person-type'),# listar tipos de personas
]