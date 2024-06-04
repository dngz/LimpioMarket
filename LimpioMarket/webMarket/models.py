from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.contrib.auth.models import User

class MiAdministradorDeUsuarios(BaseUserManager):
    def crear_usuario(self, nombre_usuario, contrasena=None, **extra_fields):
        if not nombre_usuario:
            raise ValueError('Los usuarios deben tener un nombre de usuario')

        usuario = self.model(nombre_usuario=nombre_usuario, **extra_fields)
        usuario.set_password(contrasena)
        usuario.save(using=self._db)
        return usuario

    def crear_superusuario(self, nombre_usuario, contrasena):
        usuario = self.crear_usuario(nombre_usuario, contrasena=contrasena, es_administrador=True)
        usuario.save(using=self._db)
        return usuario

class Usuario(AbstractBaseUser):
    nombre_usuario = models.CharField(max_length=30, unique=True)
    contrasena = models.CharField(max_length=128)
    rut = models.CharField(max_length=10)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=100)
    nombre_completo = models.CharField(max_length=100)
    esta_activo = models.BooleanField(default=True)
    es_administrador = models.BooleanField(default=False)

    objects = MiAdministradorDeUsuarios()

    USERNAME_FIELD = 'nombre_usuario'
    REQUIRED_FIELDS = ['contrasena', 'rut', 'email', 'telefono', 'direccion', 'nombre_completo']

    def __str__(self):
        return self.nombre_usuario

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.es_administrador

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nombre

class OrdenDeCompra(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    envio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Orden de Compra #{self.id}"

class DetallePedido(models.Model):
    orden_de_compra = models.ForeignKey(OrdenDeCompra, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()


class CarritoDeCompra(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)