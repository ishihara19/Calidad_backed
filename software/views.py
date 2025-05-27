from rest_framework import generics
from .models import Software
from .serializers import SoftwareSerializer
from .permissions import SoftwarePermission

class SoftwareListCreateView(generics.ListCreateAPIView):
    queryset = Software.objects.all()
    serializer_class = SoftwareSerializer
    permission_classes = [SoftwarePermission]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Software.objects.all()
        if user.groups.filter(name='Usuarios_Empresa').exists():
            # Solo los de su empresa
            return queryset.filter(empresa=user.empresa)
        return queryset

class SoftwareRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Software.objects.all()
    serializer_class = SoftwareSerializer
    permission_classes = [SoftwarePermission]