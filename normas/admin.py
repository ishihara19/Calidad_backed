from django.contrib import admin
from .models import Norma, Caracteristica, SubCaracteristica, CalificacionSubCaracteristica

admin.site.register(Norma)
admin.site.register(Caracteristica)
admin.site.register(SubCaracteristica)
admin.site.register(CalificacionSubCaracteristica)