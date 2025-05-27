from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from users.models import CustomUser
from normas.models import Norma

class Command(BaseCommand):
    help = 'Crea grupos por defecto con sus permisos'

    def handle(self, *args, **options):
        admin_group, _ = Group.objects.get_or_create(name='Administradores')
        evaluador_group, _ = Group.objects.get_or_create(name='Evaluadores')
        empresa_group, _ = Group.objects.get_or_create(name='Usuarios_Empresa')

        # Content types
        user_content_type = ContentType.objects.get_for_model(CustomUser)
        norma_content_type = ContentType.objects.get_for_model(Norma)
        
        # Asignar permisos a Administradores
        admin_perms = Permission.objects.filter(
            content_type__in=[user_content_type, norma_content_type]
        )
        admin_group.permissions.set(admin_perms)
        
        # Permisos para Evaluadores
        evaluador_perms = list(Permission.objects.filter(
            content_type=user_content_type,
            codename='view_customuser'
        ))
        evaluador_perms.extend(Permission.objects.filter(
            content_type=norma_content_type,
            codename__in=['view_norma', 'can_review_norma']
        ))
        evaluador_group.permissions.set(evaluador_perms)
        
        # Permisos para Usuarios Empresa
        empresa_perms = Permission.objects.filter(
            content_type=norma_content_type,
            codename__in=['view_norma']
        )
        empresa_group.permissions.set(empresa_perms)
        
        self.stdout.write(self.style.SUCCESS('Grupos y permisos creados exitosamente'))