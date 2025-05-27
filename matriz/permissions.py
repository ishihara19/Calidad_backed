# matriz/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class MatrizRiesgoPermission(BasePermission):
    """
    Permisos para matrices de riesgo según el rol del usuario:
    - Administradores: Acceso total
    - Evaluadores: Pueden crear/editar matrices de su empresa
    - Usuarios_Empresa: Solo pueden ver matrices de su empresa
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Administradores tienen acceso total
        if user.groups.filter(name='Administradores').exists():
            return True
        
        # Evaluadores pueden crear y editar matrices de su empresa
        if user.groups.filter(name='Evaluadores').exists():
            return True
        
        # Usuarios empresa solo pueden ver (lectura)
        if user.groups.filter(name='Usuarios_Empresa').exists():
            return request.method in SAFE_METHODS
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Administradores tienen acceso total
        if user.groups.filter(name='Administradores').exists():
            return True
        
        # Verificar que la matriz pertenece a la empresa del usuario
        if hasattr(user, 'empresa') and user.empresa:
            if obj.empresa != user.empresa:
                return False
        else:
            return False
        
        # Evaluadores pueden editar matrices de su empresa
        if user.groups.filter(name='Evaluadores').exists():
            return True
        
        # Usuarios empresa solo pueden ver
        if user.groups.filter(name='Usuarios_Empresa').exists():
            return request.method in SAFE_METHODS
        
        return False


class CanCreateMatriz(BasePermission):
    """
    Permiso específico para crear matrices de riesgo
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Solo administradores y evaluadores pueden crear matrices
        return user.groups.filter(
            name__in=['Administradores', 'Evaluadores']
        ).exists()


class CanEditOwnMatriz(BasePermission):
    """
    Permiso para editar matrices propias
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Administradores pueden editar cualquier matriz
        if user.groups.filter(name='Administradores').exists():
            return True
        
        # Los evaluadores solo pueden editar matrices de su empresa
        if user.groups.filter(name='Evaluadores').exists():
            return (
                hasattr(user, 'empresa') and 
                user.empresa and 
                obj.empresa == user.empresa
            )
        
        return False


class MatrizEmpresaPermission(BasePermission):
    """
    Validar que la matriz pertenece a la empresa del usuario
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Verificar que el usuario tenga empresa asignada
        return hasattr(request.user, 'empresa') and request.user.empresa
    
    def validate_matriz_empresa(self, user, matriz):
        """
        Método auxiliar para validar matriz-empresa
        """
        if not matriz:
            return True  # Se validará en el serializer
        
        return matriz.empresa == user.empresa