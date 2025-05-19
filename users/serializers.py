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
from empresa.models import Empresa

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
    codigo_empresa = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=20, label="Código de Empresa")
    empresa = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = CustomUser
        fields = [
            'document', 'first_name', 'last_name', 'email', 
            'document_type', 'person_type', 'phone', 'address',
            'password', 'is_active','date_joined',
            'codigo_empresa', 
            'empresa', 
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
            codigo_empresa_str = validated_data.pop('codigo_empresa', None)
            empresa_obj = None

            if codigo_empresa_str: # Si se proporcionó un código de empresa
                try:
                    empresa_obj = Empresa.objects.get(codigo_empresa=codigo_empresa_str)
                except Empresa.DoesNotExist:
                    # Si el código de empresa se proporciona pero no es válido, lanzamos un error.
                    # Esto detendrá la creación del usuario y devolverá un error 400.
                    raise serializers.ValidationError({"codigo_empresa": "El código de empresa proporcionado no es válido o no existe."})
        
            validated_data['password'] = make_password(validated_data['password'])
            validated_data['is_active'] = True           
            if empresa_obj:
                validated_data['empresa'] = empresa_obj # Asignamos la instancia de la empresa encontrada
            
            # Si 'empresa' en CustomUser es null=True, blank=True y no se proporciona un código_empresa válido,
            # el usuario se creará sin empresa. Si 'empresa' es obligatoria (null=False),
            # entonces deberías hacer 'required=True' en 'codigo_empresa' y el error de arriba se manejaría.
            user = CustomUser.objects.create(**validated_data)
            return user
    def update(self, instance, validated_data):
        """
        Actualiza un usuario. Opcionalmente, puede actualizar la empresa.
        """
        codigo_empresa_str = validated_data.pop('codigo_empresa', None)
        
        if codigo_empresa_str:
            try:
                empresa_obj = Empresa.objects.get(codigo_empresa=codigo_empresa_str)
                instance.empresa = empresa_obj
            except Empresa.DoesNotExist:
                raise serializers.ValidationError({"codigo_empresa": "El código de empresa proporcionado no es válido o no existe."})
        elif 'codigo_empresa' in self.initial_data and not codigo_empresa_str: 
            # Si se envía explícitamente un codigo_empresa vacío/nulo, desvincular empresa
            instance.empresa = None

        # Manejo de la contraseña (si se actualiza)
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
            
        return super().update(instance, validated_data)    
        
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
                  