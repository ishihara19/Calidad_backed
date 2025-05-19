from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError
from .models import (
    CustomUser,
    DocumentType,
    PersonType
)
from .serializers import(
    CustomUserSerializer,
    DocumentTypeSerializer,
    PersonTypeSerializer
)

class CustomUserCreateView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [] # Ajusta según tu necesidad

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e: # Esto capturará errores del serializer.validate() o serializer.create()
            print("errors en la vista:", e.detail) # Para debugging en el servidor
            return Response(
                {
                    "message": "Error al registrar el usuario.",
                    # serializer.errors ya contendrá el error de codigo_empresa si se lanzó desde create
                    "errors": serializer.errors if hasattr(serializer, 'errors') else e.detail 
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Si la validación es exitosa, perform_create llamará a serializer.save(),
        # lo cual a su vez llama a serializer.create() con los validated_data.
        self.perform_create(serializer) 
        
        headers = self.get_success_headers(serializer.data)

        return Response(
            {
                "message": "Usuario registrado exitosamente.",
                "user": serializer.data # serializer.data contendrá el usuario creado, incluyendo la empresa si se vinculó
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )
class DocumentTypeListView(generics.ListAPIView):
    queryset = DocumentType.objects.all()
    serializer_class= DocumentTypeSerializer
    permission_classes= [AllowAny]        

class PersonTypeListView(generics.ListAPIView):
    queryset = PersonType.objects.all()
    serializer_class= PersonTypeSerializer   
    permission_classes= [AllowAny]          