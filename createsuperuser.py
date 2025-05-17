import os
import django

# Configuración del entorno de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "API_C.settings")
django.setup()

from django.contrib.auth import get_user_model
from users.models import DocumentType, PersonType
User = get_user_model()

document_type = os.environ.get("DJANGO_SUPERUSER_DOCUMENT_TYPE" )
person_type = os.environ.get("DJANGO_SUPERUSER_PERSON_TYPE" ) 

instance_document_type = DocumentType.objects.get(documentTypeId=document_type)
         
instance_person_type = PersonType.objects.get(personTypeId=person_type)    

# Datos del superusuario
superuser_data = {
   "document": os.environ.get("DJANGO_SUPERUSER_DOCUMENT"),
    "first_name": os.environ.get("DJANGO_SUPERUSER_FIRST_NAME"),
    "last_name": os.environ.get("DJANGO_SUPERUSER_LAST_NAME"),
    "email": os.environ.get("DJANGO_SUPERUSER_EMAIL"),
    "phone": os.environ.get("DJANGO_SUPERUSER_PHONE"),
    "address": os.environ.get("DJANGO_SUPERUSER_ADDRESS"),
    "password": os.environ.get("DJANGO_SUPERUSER_PASSWORD" ),
    "document_type": instance_document_type,
    "person_type": instance_person_type,      
    }

if None in superuser_data.values():
    print("❌ Error: Faltan variables de entorno para el superusuario.")
    exit(1)

# Verificar si el superusuario ya existe
if not User.objects.filter(document=superuser_data["document"]).exists():
    User.objects.create_superuser(**superuser_data)
    print("✅ Superusuario creado con éxito.")
else:
    print("⚠ El superusuario ya existe.")