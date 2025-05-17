from .models import CustomUser
from rest_framework.exceptions import NotFound
def validate_user_exist(email):
        """
        Verifica si el usuario con el documento proporcionado existe.
        """       
        user = CustomUser.objects.filter(email=email).first()
        if not user:
            raise NotFound("Usuario no encontrado.")       
        return user