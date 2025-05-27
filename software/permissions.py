from rest_framework import permissions

class SoftwarePermission(permissions.BasePermission):
    """
    - Administradores: pueden listar y crear.
    - Evaluadores: solo pueden listar.
    - Usuarios_Empresa: solo pueden listar los de su empresa.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False

        if user.groups.filter(name='Administradores').exists():
            return True  # Puede listar y crear

        if user.groups.filter(name='Evaluadores').exists():
            return request.method in permissions.SAFE_METHODS  # Solo listar

        if user.groups.filter(name='Usuarios_Empresa').exists():
            return request.method in permissions.SAFE_METHODS  # Solo listar

        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.groups.filter(name='Usuarios_Empresa').exists():
            # Solo puede ver los de su empresa
            return obj.empresa == user.empresa
        return True