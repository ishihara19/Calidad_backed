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
    permission_classes = []  # Ajusta según tu necesidad

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            print("errors",e.detail)
            return Response(
                {
                    "message": "Error al registrar el usuario.",
                    "errors": serializer.errors  # También puedes usar `e.detail` si prefieres
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(
            {
                "message": "Usuario registrado exitosamente.",
                "user": serializer.data
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