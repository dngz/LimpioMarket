from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario, Producto, OrdenDeCompra, DetallePedido
from .forms import UsuarioCreacionForm, UsuarioCambioForm

class UsuarioAdmin(BaseUserAdmin):
    form = UsuarioCambioForm
    add_form = UsuarioCreacionForm

    list_display = ('nombre_usuario', 'email', 'rut', 'telefono', 'direccion', 'nombre_completo', 'is_active', 'is_staff')
    list_filter = ('is_staff',)

    fieldsets = (
        (None, {'fields': ('nombre_usuario', 'password')}),
        ('Información personal', {'fields': ('rut', 'email', 'telefono', 'direccion', 'nombre_completo')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('nombre_usuario', 'password1', 'password2', 'rut', 'email', 'telefono', 'direccion', 'nombre_completo', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
    )

    search_fields = ('nombre_usuario', 'email')
    ordering = ('nombre_usuario',)
    filter_horizontal = ('groups', 'user_permissions',)

class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio')
    search_fields = ('nombre',)
    ordering = ('nombre',)

class OrdenDeCompraAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha', 'subtotal', 'total', 'descuento', 'envio')
    search_fields = ('usuario__nombre_usuario',)
    ordering = ('-fecha',)

class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ('orden_de_compra', 'producto', 'cantidad')
    search_fields = ('orden_de_compra__id', 'producto__nombre')
    ordering = ('orden_de_compra',)

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Producto, ProductoAdmin)
admin.site.register(OrdenDeCompra, OrdenDeCompraAdmin)
admin.site.register(DetallePedido, DetallePedidoAdmin)
