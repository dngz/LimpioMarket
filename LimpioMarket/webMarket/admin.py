from django.contrib import admin
from .models import Producto, OrdenDeCompra

# Register your models here.

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cantidad', 'precio')
    search_fields = ('nombre',)

@admin.register(OrdenDeCompra)
class OrdenDeCompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'rut', 'direccion', 'correo', 'fecha', 'total')
    search_fields = ('rut', 'direccion', 'correo')
    date_hierarchy = 'fecha'
    filter_horizontal = ('productos',)
    
    def total(self, obj):
        return obj.total()

    total.short_description = 'Total'