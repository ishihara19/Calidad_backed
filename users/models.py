from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from empresa.models import Empresa
class UserManager(BaseUserManager):
    """
    Administrador de usuarios personalizado para la gestión de usuarios y superusuarios.
    """

    def create_user(self, document, first_name, last_name, email, phone, document_type, person_type, password=None, **extra_fields):
        
        if not document:
            raise ValueError("El documento es obligatorio")
        if not email:
            raise ValueError("El correo electrónico es obligatorio")
        if not phone:
            raise ValueError("El número de teléfono es obligatorio")
         # Convertir a instancia si es un ID
        if isinstance(document_type, int):
            document_type = DocumentType.objects.get(documentTypeId=document_type)
         
        if isinstance(person_type, int):
            person_type = PersonType.objects.get(personTypeId=person_type)    

        email = self.normalize_email(email)
        user = self.model(
            document=document,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            document_type=document_type,
            person_type=person_type,            
            **extra_fields
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, document, first_name, last_name, email, phone, document_type, person_type, password=None, **extra_fields):
        """
        Crea y guarda un superusuario con privilegios administrativos.

        Args:
            document (str): Documento del superusuario.
            first_name (str): Nombre del superusuario.
            last_name (str): Apellido del superusuario.
            email (str): Correo electrónico único del superusuario.
            phone (str): Número de teléfono del superusuario.
            password (str, optional): Contraseña del superusuario.
            **extra_fields: Campos adicionales.

        Returns:
            CustomUser: Superusuario creado.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)       

        return self.create_user(document, first_name, last_name, email, phone,document_type, person_type, password, **extra_fields)

class CustomUser(AbstractUser):
    """
    Modelo de usuario personalizado con autenticación basada en el documento.
    """

    document = models.CharField(max_length=12, unique=True, db_index=True, verbose_name="Documento")
    first_name = models.CharField(max_length=50, db_index=True, verbose_name="Nombre")
    last_name = models.CharField(max_length=50, db_index=True, verbose_name="Apellido")
    email = models.EmailField(unique=True, db_index=True, verbose_name="Correo Electrónico")
    document_type = models.ForeignKey('DocumentType', on_delete=models.CASCADE, related_name="users_with_document_type", null=True, db_index=True, verbose_name="Tipo de Documento")
    person_type = models.ForeignKey('PersonType', on_delete=models.CASCADE, related_name="users_with_person_type", null=True, db_index=True, verbose_name="Tipo de Persona")
    phone = models.CharField(max_length=10, db_index=True, verbose_name="Teléfono")
    address = models.CharField(max_length=200, db_index=True, verbose_name="Dirección")
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='usuarios', null=True, blank=True, verbose_name="Empresa")
   

    username = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['document','first_name', 'last_name','person_type','document_type', 'phone', 'address' ]

    objects = UserManager()
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
    
    def save(self, *args, **kwargs):
        if not self.empresa:
            print("XD")
        super().save(*args, **kwargs)        
                 

    def __str__(self):
        return f"{self.document} - {self.first_name} {self.last_name}" 
    
class DocumentType(models.Model):
    """
    Modelo para los tipos de documentos de identificación.
    """

    documentTypeId = models.AutoField(primary_key=True, verbose_name="ID de Tipo de Documento")
    typeName = models.CharField(max_length=50, verbose_name="Nombre del Tipo de Documento")

    def __str__(self):
        return f"{self.documentTypeId} - {self.typeName}"
    
    class Meta:
        verbose_name = "Tipo de documento"
        verbose_name_plural = "Tipos de documento"

class PersonType(models.Model):
    """
    Modelo para definir tipos de personas (ej. Natural, Jurídica).
    """

    personTypeId = models.AutoField(primary_key=True, verbose_name="ID de Tipo de Persona")
    typeName = models.CharField(max_length=20, verbose_name="Nombre del Tipo de Persona")

    def __str__(self):
        return f"{self.personTypeId} - {self.typeName}"
    
    class Meta:
        verbose_name = "Tipos de persona"
        verbose_name_plural = "Tipos de persona"