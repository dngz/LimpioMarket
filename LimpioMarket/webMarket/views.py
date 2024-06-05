from django.shortcuts import render, redirect
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
def index(request):
    return render(request, 'index.html')

@login_required
def orden_de_compra(request):
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

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                messages.success(request, f"¡Bienvenido, {username}!")
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

    return render(request, 'lista.html', {'ordenes_con_factura': ordenes_con_factura})