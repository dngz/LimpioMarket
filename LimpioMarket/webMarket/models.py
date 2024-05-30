from django.db import models

# Create your models here.
class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    cantidad = models.IntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nombre

class OrdenDeCompra(models.Model):
    productos = models.ManyToManyField(Producto, related_name='orden_compra')
    fecha = models.DateTimeField(auto_now_add=True)
    direccion = models.CharField(max_length=255, default='')
    correo = models.EmailField(default='')
    rut = models.CharField(max_length=10, default='')

    def total(self):
        return sum(producto.precio * producto.cantidad for producto in self.productos.all())

    def __str__(self):
        return f"Orden de Compra #{self.id} - {self.rut}"