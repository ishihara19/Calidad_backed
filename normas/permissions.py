from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrReadOnly(BasePermission):
    """
    Permite acceso completo solo a usuarios admin (is_staff),
    otros usuarios solo lectura (GET, HEAD, OPTIONS).
    
    - Usuarios anónimos: Solo lectura
    - Usuarios autenticados no-admin: Solo lectura  
    - Usuarios admin (is_staff=True): Acceso completo
    """

    def has_permission(self, request, view):
        # ✅ MEJORADO: Permitir métodos seguros para cualquier usuario (incluso anónimos)
        if request.method in SAFE_METHODS:
            return True
        
        # ✅ MEJORADO: Validar que el usuario existe, está autenticado Y es staff
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff
        )

    # ✅ AGREGADO: Método para permisos a nivel de objeto (opcional pero recomendado)
    def has_object_permission(self, request, view, obj):
        """
        Permisos a nivel de objeto individual.
        Útil si necesitas lógica específica por objeto en el futuro.
        """
        # Métodos seguros permitidos para todos
        if request.method in SAFE_METHODS:
            return True
        
        # Solo staff puede modificar objetos específicos
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff
        )


# ✅ AGREGADO: Permiso adicional útil para tu aplicación
class IsOwnerOrReadOnly(BasePermission):
    """
    Permite editar solo al propietario del objeto, otros usuarios solo lectura.
    Útil para CalificacionSubCaracteristica donde usuarios pueden editar sus propias calificaciones.
    """
    
    def has_object_permission(self, request, view, obj):
        # Métodos seguros permitidos para todos
        if request.method in SAFE_METHODS:
            return True
        
        # Permisos de escritura solo para el propietario del objeto
        return (
            request.user and 
            request.user.is_authenticated and 
            obj.usuario == request.user
        )


# ✅ AGREGADO: Permiso específico para empresas
class IsOwnerOrAdminOrReadOnly(BasePermission):
    """
    Combina ambos permisos: 
    - Admins pueden hacer todo
    - Propietarios pueden editar sus objetos
    - Otros usuarios solo lectura
    """
    
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Métodos seguros permitidos para todos
        if request.method in SAFE_METHODS:
            return True
        
        # Verificar autenticación
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Admins pueden hacer todo
        if request.user.is_staff:
            return True
        
        # Propietarios pueden editar sus objetos
        return hasattr(obj, 'usuario') and obj.usuario == request.user
# ...existing code...

class CanManageNorma(BasePermission):
    """
    Permiso personalizado para gestión de normas según el rol del usuario:
    - Ver normas: cualquier usuario autenticado
    - Crear normas: usuarios con permiso can_create_norma
    - Aprobar normas: usuarios con permiso can_approve_norma
    - Revisar normas: usuarios con permiso can_review_norma
    """
    def has_permission(self, request, view):
        # Métodos seguros (GET, HEAD, OPTIONS) permitidos para usuarios autenticados
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Verificar permisos específicos según la acción
        if not request.user.is_authenticated:
            return False

        if view.action == 'create':
            return request.user.has_perm('normas.can_create_norma')
        elif view.action == 'approve':
            return request.user.has_perm('normas.can_approve_norma')
        elif view.action == 'review':
            return request.user.has_perm('normas.can_review_norma')
        elif view.action in ['update', 'partial_update', 'destroy']:
            return request.user.is_staff
            
        return False

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
            
        # Solo el creador o administradores pueden modificar
        return (
            request.user.is_staff or 
            (hasattr(obj, 'creado_por') and obj.creado_por == request.user)
        )