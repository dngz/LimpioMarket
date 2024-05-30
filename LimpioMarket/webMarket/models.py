from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

class MiAdministradorDeUsuarios(BaseUserManager):
    def crear_usuario(self, nombre_usuario, contrasena=None):
        if not nombre_usuario:
            raise ValueError('Los usuarios deben tener un nombre de usuario')

        usuario = self.model(nombre_usuario=nombre_usuario)
        usuario.set_password(contrasena)
        usuario.save(using=self._db)
        return usuario

    def crear_superusuario(self, nombre_usuario, contrasena):
        usuario = self.crear_usuario(nombre_usuario, contrasena=contrasena)
        usuario.es_administrador = True
        usuario.save(using=self._db)
        return usuario

class Usuario(AbstractBaseUser):
    nombre_usuario = models.CharField(max_length=30, unique=True)
    esta_activo = models.BooleanField(default=True)
    es_administrador = models.BooleanField(default=False)

    objects = MiAdministradorDeUsuarios()

    USERNAME_FIELD = 'nombre_usuario'
    REQUIRED_FIELDS = []

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
    cantidad = models.IntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nombre

    def precio_total(self):
        return self.cantidad * self.precio

class OrdenDeCompra(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)  # Nuevo campo de usuario
    productos = models.ManyToManyField(Producto, related_name='orden_compra')
    fecha = models.DateTimeField(auto_now_add=True)
    direccion = models.CharField(max_length=255, default='')
    correo = models.EmailField(default='')
    rut = models.CharField(max_length=10, default='')

    def total(self):
        return sum(producto.precio_total() for producto in self.productos.all())

    def __str__(self):
        return f"Orden de Compra #{self.id} - {self.rut}"