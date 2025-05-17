def create_default_person_types(sender, **kwargs):
    from .models import PersonType
    from django.db import transaction

    try:
        default_types = {
            1: "Natural",
            2: "Jurídica",           
        }

        with transaction.atomic():
            for person_id, name in default_types.items():
                PersonType.objects.update_or_create(
                    personTypeId=person_id,
                    defaults={"typeName": name}
                )

    except Exception as e:
        print(f"Error creando tipos de documento: {e}")
        
def create_default_document_types(sender, **kwargs):
    from .models import DocumentType
    from django.db import transaction

    try:
        default_types = {
            1: "Cédula de Ciudadanía (CC)",
            2: "Número de Identificación Tributaria (NIT)",
            3: "Cédula de Extranjería (CE)",                  
        }

        with transaction.atomic():
            for doc_id, name in default_types.items():
                DocumentType.objects.update_or_create(
                    documentTypeId=doc_id,
                    defaults={"typeName": name}
                )

    except Exception as e:
        print(f"Error creando tipos de documento: {e}")  