from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotFound,PermissionDenied
from .models import CustomUser
from .serializers import LoginSerializer
from rest_framework.authtoken.models import Token

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):        
        try:
            serializer = LoginSerializer(data=request.data)
            
            if serializer.is_valid(raise_exception=True):
                data = serializer.validated_data
                email = data.get('email')               
               
                # Buscar usuario y eliminar token previo
                user_instance = CustomUser.objects.filter(email=email).first()
                token, created = Token.objects.get_or_create(user=user_instance)                
                full_name = user_instance.get_full_name()
                user = {
                    "nombre": full_name,
                    "id": user_instance.document,
                    "email": user_instance.email,
                    "token":token.key,
                    "rol": list(user_instance.groups.values_list('name', flat=True))
                }               

                return Response( {"user": user}, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except NotFound as e:
            return Response({"error": e.detail}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"error": e.detail}, status=status.HTTP_403_FORBIDDEN) 
        except Exception as e:
            return Response(
                {"error": "Unexpected error.", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 
class LogoutView(APIView):  

    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        if not request.user.is_authenticated:
            return Response(
                {"error": "No estás autenticado. Por favor, inicia sesión."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            # Eliminar el token del usuario autenticado
            request.user.auth_token.delete()
            return Response({"message": "Sesión cerrada correctamente."}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": "No se pudo cerrar la sesión.", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)            