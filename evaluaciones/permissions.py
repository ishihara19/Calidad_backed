from rest_framework.permissions import BasePermission, SAFE_METHODS

class EvaluacionPermission(BasePermission):
    """
    Permisos para evaluaciones según el rol del usuario:
    - Administradores: Acceso total
    - Evaluadores: Pueden crear/ver evaluaciones de su empresa
    - Usuarios_Empresa: Solo pueden ver sus propias evaluaciones
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Administradores tienen acceso total
        if user.groups.filter(name='Administradores').exists():
            return True
        
        # Evaluadores pueden crear y ver evaluaciones de su empresa
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
        
        # Evaluadores pueden acceder a evaluaciones de su empresa
        if user.groups.filter(name='Evaluadores').exists():
            return obj.empresa == user.empresa
        
        # Usuarios empresa solo pueden ver sus propias evaluaciones
        if user.groups.filter(name='Usuarios_Empresa').exists():
            return obj.evaluador == user and request.method in SAFE_METHODS
        
        return False

class CanCreateEvaluacion(BasePermission):
    """
    Permiso específico para crear evaluaciones
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Solo administradores y evaluadores pueden crear evaluaciones
        return user.groups.filter(
            name__in=['Administradores', 'Evaluadores']
        ).exists()

class CanEditOwnEvaluacion(BasePermission):
    """
    Permiso para editar evaluaciones propias
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Administradores pueden editar cualquier evaluación
        if user.groups.filter(name='Administradores').exists():
            return True
        
        # Los evaluadores solo pueden editar sus propias evaluaciones
        # y solo si están en estado borrador o en_progreso
        if user.groups.filter(name='Evaluadores').exists():
            return (
                obj.evaluador == user and 
                obj.estado in ['borrador', 'en_progreso']
            )
        
        return False

class SoftwareEmpresaPermission(BasePermission):
    """
    Validar que el software pertenece a la empresa del usuario
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Verificar que el usuario tenga empresa asignada
        return hasattr(request.user, 'empresa') and request.user.empresa
    
    def validate_software_empresa(self, user, software):
        """
        Método auxiliar para validar software-empresa
        """
        if not software:
            return True  # Se validará en el serializer
        
        return software.empresa == user.empresa