from django.contrib import admin
from .models import Usuario, Producto, OrdenDeCompra, DetallePedido

class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('nombre_usuario', 'email', 'rut', 'telefono', 'direccion', 'nombre_completo', 'esta_activo', 'es_administrador')
    search_fields = ('nombre_usuario', 'email')
    ordering = ('nombre_usuario',)

class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio','cantidad')
    search_fields = ('nombre',)
    ordering = ('nombre',)

class OrdenDeCompraAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha', 'subtotal', 'total', 'descuento', 'envio')
    search_fields = ('usuario__nombre_usuario',)
    ordering = ('-fecha',)

class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ('orden_de_compra', 'producto')
    search_fields = ('orden_de_compra__id', 'producto__nombre')
    ordering = ('orden_de_compra',)

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Producto, ProductoAdmin)
admin.site.register(OrdenDeCompra, OrdenDeCompraAdmin)
admin.site.register(DetallePedido, DetallePedidoAdmin)