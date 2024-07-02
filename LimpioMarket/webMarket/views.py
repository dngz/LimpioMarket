from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.messages import get_messages
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.db import transaction
import json
from .models import Usuario, CarritoDeCompra, Producto, OrdenDeCompra, DetallePedido, Factura
from django.db.models import F, Sum
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.contrib.auth import logout as auth_logout
from django.views.decorators.csrf import csrf_exempt

def index(request):
    return render(request, 'index.html')

@login_required
def orden_de_compra(request):
    if request.user.is_superuser:
        messages.error(request, "Los superusuarios no pueden crear órdenes de compra.")
        return redirect('lista_productos')

    try:
        usuario = Usuario.objects.get(nombre_usuario=request.user.nombre_usuario)
    except Usuario.DoesNotExist:
        return HttpResponseForbidden("El usuario no existe.")
    
    carrito = CarritoDeCompra.objects.filter(usuario=usuario)
    productos = [{'nombre': item.producto.nombre, 'precio': item.producto.precio, 'cantidad': item.cantidad} for item in carrito]
    total_precio = sum([item.producto.precio * item.cantidad for item in carrito])

    return render(request, 'orden_compra.html', {'productos': productos, 'total_precio': total_precio})

@login_required
def guardar_orden_de_compra(request):
    if request.user.is_superuser:
        return JsonResponse({'error': 'Los superusuarios no pueden crear órdenes de compra.'})

    if request.method == 'POST':
        direccion = request.POST.get('direccion', '')
        productos_json = request.POST.get('productos')

        productos = json.loads(productos_json)

        try:
            usuario = Usuario.objects.get(nombre_usuario=request.user.nombre_usuario)
        except Usuario.DoesNotExist:
            return JsonResponse({'error': 'Usuario no encontrado.'})

        subtotal = sum([int(producto['cantidad']) * int(producto['precio']) for producto in productos])
        total = subtotal + (3000 if direccion else 0)

        try:
            with transaction.atomic():
                orden_compra = OrdenDeCompra.objects.create(
                    usuario=usuario,
                    direccion=direccion,
                    subtotal=subtotal,
                    total=total
                )

                for producto_data in productos:
                    producto, created = Producto.objects.get_or_create(
                        nombre=producto_data['nombre'],
                        defaults={'precio': producto_data['precio']}
                    )
                    DetallePedido.objects.create(
                        orden_de_compra=orden_compra,
                        producto=producto,
                        cantidad=int(producto_data['cantidad'])
                    )

            return JsonResponse({'success': '¡La orden de compra se ha guardado correctamente!'})
        except Exception as e:
            return JsonResponse({'error': f'Ocurrió un error al guardar la orden de compra: {str(e)}'})

    return JsonResponse({'error': 'Método no permitido.'})

def visualizar_orden(request, orden_id):
    orden = get_object_or_404(OrdenDeCompra, id=orden_id)
    detalles = DetallePedido.objects.filter(orden_de_compra=orden)
    return render(request, 'visualizar_orden.html', {
        'orden': orden,
        'detalles': detalles,
    })

@csrf_exempt
def actualizar_orden(request, orden_id):
    if request.method == 'POST':
        orden = get_object_or_404(OrdenDeCompra, id=orden_id)
        detalles = DetallePedido.objects.filter(orden_de_compra=orden)

        try:
            # Actualizar información del usuario
            usuario = orden.usuario
            usuario.nombre_usuario = request.POST['nombre_usuario']
            usuario.nombre_completo = request.POST['nombre_completo']
            usuario.rut = request.POST['rut']
            usuario.email = request.POST['email']
            usuario.telefono = request.POST['telefono']
            usuario.direccion = request.POST['direccion']
            usuario.save()

            # Bandera para detectar cambios
            cambios_realizados = False

            # Actualizar los detalles de la orden y los productos
            for detalle in detalles:
                cantidad = request.POST.get(f'cantidad_{detalle.id}')
                if cantidad and int(cantidad) != detalle.cantidad:
                    detalle.cantidad = int(cantidad)
                    cambios_realizados = True

                # Actualizar nombre y precio del producto si están presentes en el POST data
                nuevo_nombre = request.POST.get(f'nombre_producto_{detalle.id}')
                nuevo_precio = request.POST.get(f'precio_producto_{detalle.id}')

                if nuevo_nombre and nuevo_nombre != detalle.producto.nombre:
                    detalle.producto.nombre = nuevo_nombre
                    cambios_realizados = True
                if nuevo_precio and int(nuevo_precio) != detalle.producto.precio:
                    detalle.producto.precio = int(nuevo_precio)
                    cambios_realizados = True

                detalle.producto.save()
                detalle.save()

            if cambios_realizados:
                # Calcular los totales actualizados
                subtotal_actualizado = sum(detalle.cantidad * detalle.producto.precio for detalle in detalles)
                impuestos_actualizados = int(subtotal_actualizado * 0.19)
                total_actualizado = subtotal_actualizado + impuestos_actualizados

                # Actualizar la orden
                orden.subtotal = subtotal_actualizado
                orden.total = total_actualizado
                orden.save()

                # Actualizar la factura asociada a la orden, si existe
                factura = Factura.objects.filter(orden_de_compra=orden).first()
                if factura:
                    factura.subtotal = subtotal_actualizado
                    factura.impuestos = impuestos_actualizados
                    factura.total = total_actualizado
                    factura.condicion = 'rectificado'  # Cambiar la condición a "rectificado"
                    factura.save()

                return JsonResponse({'success': 'Orden actualizada con éxito.'})
            else:
                return JsonResponse({'success': 'No se realizaron cambios en la orden.'})

        except Exception as e:
            return JsonResponse({'error': str(e)})
    else:
        return JsonResponse({'error': 'Método no permitido.'})

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('lista_productos')
            else:
                messages.error(request, "Usuario o contraseña incorrectos.")
        else:
            messages.error(request, "Formulario inválido.")
    else:
        form = AuthenticationForm()

    storage = get_messages(request)
    message_list = [{'message': message.message, 'tags': message.tags} for message in storage]
    message_json = mark_safe(json.dumps(message_list))

    return render(request, 'login.html', {'form': form, 'messages': message_json})

@login_required
def lista_productos(request):
    usuario = request.user

    if request.user.is_superuser:
        # Si el usuario es un superusuario, simplemente pasamos una lista vacía de órdenes
        ordenes_con_factura = []
    else:
        try:
            usuario = Usuario.objects.get(nombre_usuario=usuario.nombre_usuario)
        except Usuario.DoesNotExist:
            return HttpResponseForbidden("El usuario no existe.")

        ordenes = OrdenDeCompra.objects.filter(usuario=usuario).prefetch_related('detalles__producto')
        ordenes_con_factura = []

        for orden in ordenes:
            impuestos = int(orden.subtotal * 0.19)
            total_factura = orden.subtotal + impuestos

            factura, created = Factura.objects.get_or_create(
                orden_de_compra=orden,
                defaults={
                    'numero_factura': get_random_string(length=10, allowed_chars='0123456789'),
                    'subtotal': orden.subtotal,
                    'impuestos': impuestos,
                    'total': total_factura,
                    'fecha_emision': timezone.now()
                }
            )
            if not created:
                if factura.total != total_factura:
                    factura.subtotal = orden.subtotal
                    factura.impuestos = impuestos
                    factura.total = total_factura
                    factura.save()

            detalles_con_totales = [
                {
                    'producto': detalle.producto,
                    'cantidad': detalle.cantidad,
                    'total': detalle.cantidad * detalle.producto.precio
                }
                for detalle in orden.detalles.all()
            ]

            ordenes_con_factura.append({
                'orden': orden,
                'factura': factura,
                'total': orden.detalles.aggregate(total=Sum(F('cantidad') * F('producto__precio')))['total'] or 0,
                'detalles': detalles_con_totales
            })

    return render(request, 'lista.html', {'ordenes_con_factura': ordenes_con_factura, 'es_superusuario': request.user.is_superuser})

def logout_view(request):
    auth_logout(request)
    return redirect('LOGIN') 