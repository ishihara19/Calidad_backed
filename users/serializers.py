from rest_framework import serializers
from .models import (
    CustomUser,
    DocumentType,
    PersonType
)
from .validate import validate_user_exist
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from rest_framework.authtoken.models import Token
class DocumentTypeSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo DocumentType.
    Representa los tipos de documentos disponibles.
    """
    
    class Meta:
        model = DocumentType
        fields = ['documentTypeId', 'typeName']

class PersonTypeSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo PersonType.
    Representa los tipos de personas en el sistema.
    """
    class Meta:
        model = PersonType
        fields = ['personTypeId', 'typeName']

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    document_type = serializers.PrimaryKeyRelatedField(queryset=DocumentType.objects.all(), required=True)
    person_type = serializers.PrimaryKeyRelatedField(queryset=PersonType.objects.all(), required=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'document', 'first_name', 'last_name', 'email', 
            'document_type', 'person_type', 'phone', 'address',
            'password', 'is_active','date_joined'
        ]
        read_only_fields = ('date_joined',)
        
    def validate_phone(self, value):
        """
        Verifica si el número de teléfono es válido.
        """
        if not value.isdigit():
            raise serializers.ValidationError("El telefono solo debe contener números.")
        if len(value) != 10:    
            raise serializers.ValidationError("El número de teléfono debe tener 10 dígitos.")
        return value
    
    def create(self, validated_data):
            """
            Crea un usuario nuevo sin manejar la subida de archivos.
            """
            self.validate_phone(validated_data['phone'])
            validated_data['password'] = make_password(validated_data['password'])
            validated_data['is_active'] = True           
            user = CustomUser.objects.create(**validated_data)
            
          
            return user
        
class LoginSerializer(serializers.Serializer):

    email = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')               

        user = validate_user_exist(email)              

        if not user.is_active:
            raise PermissionDenied({"detail": "Su cuenta está inactiva. Póngase en contacto con el servicio de soporte."})    
       
        # Validar la contraseña
        if not user.check_password(password):
            message = "Usuario o contraseña incorrectos."
            raise serializers.ValidationError({"detail": message})
        response_data = {}        
        user.last_login = timezone.now()
        user.save()    
        response_data['email']= user.email
        return response_data 
                  