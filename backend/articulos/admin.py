from django.contrib import admin

from .models import Articulo

admin.site.site_header = "Artículos"
admin.site.site_title = "Administrador de Microservicios de Edisa"
admin.site.index_title = "Edisa | Administrador de Microservicios"

admin.site.register(Articulo)
