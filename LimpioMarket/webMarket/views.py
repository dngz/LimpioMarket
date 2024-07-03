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
from .models import Usuario, CarritoDeCompra, Producto, OrdenDeCompra, DetallePedido, Factura,DetalleEstado, HistorialCambios
from django.db.models import F, Sum
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.contrib.auth import logout as auth_logout
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.http import JsonResponse
from django.core.paginator import Paginator

def index(request):
    return render(request, 'index.html')

@login_required
def orden_de_compra(request):
    if request.method == 'POST':
        try:
            orden = OrdenDeCompra(
                usuario=request.user,
                fecha=request.POST.get('fecha')
            )
            orden.save()
            for key in request.POST.keys():
                if key.startswith('producto_'):
                    producto_id = key.split('_')[1]
                    cantidad = int(request.POST.get(f'cantidad_{producto_id}', 0))
                    if cantidad > 0:
                        DetallePedido.objects.create(
                            orden_de_compra=orden,
                            producto_id=producto_id,
                            cantidad=cantidad
                        )
            return JsonResponse({'success': 'Orden de compra creada con éxito.'})
        except Exception as e:
            return JsonResponse({'error': f'Ocurrió un error al crear la orden de compra: {str(e)}'})

    return render(request, 'orden_compra.html')

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

@login_required
@csrf_exempt
def visualizar_orden(request, orden_id):
    orden = get_object_or_404(OrdenDeCompra, id=orden_id)
    detalles = DetallePedido.objects.filter(orden_de_compra=orden)
    
    detalles_con_totales = []
    for detalle in detalles:
        total_detalle = detalle.cantidad * detalle.producto.precio
        detalles_con_totales.append({
            'detalle': detalle,
            'total': total_detalle
        })

    contexto = {
        'orden': orden,
        'detalles': detalles_con_totales,
        'subtotal': orden.subtotal,
        'iva': orden.subtotal * 0.19,  # Suponiendo un IVA del 19%
        'descuento': orden.descuento if orden.descuento else 0,
        'envio': orden.envio if orden.envio else 0,
        'total': orden.total
    }
    return render(request, 'visualizar_orden.html', contexto)

@login_required
@csrf_exempt
def actualizar_orden(request, orden_id):
    if request.method == 'POST':
        orden = get_object_or_404(OrdenDeCompra, id=orden_id)
        detalles = DetallePedido.objects.filter(orden_de_compra=orden)
        cambios = []

        # Actualizar los detalles de los productos
        for detalle in detalles:
            cantidad_anterior = detalle.cantidad
            precio_anterior = detalle.producto.precio
            nombre_anterior = detalle.producto.nombre

            detalle.cantidad = int(request.POST.get(f'cantidad_{detalle.id}'))
            detalle.producto.precio = float(request.POST.get(f'precio_producto_{detalle.id}'))
            detalle.producto.nombre = request.POST.get(f'nombre_producto_{detalle.id}')
            detalle.producto.save()
            detalle.save()

            if cantidad_anterior != detalle.cantidad:
                cambios.append(f'Cantidad de {detalle.producto.nombre} cambiada de {cantidad_anterior} a {detalle.cantidad}')
            if precio_anterior != detalle.producto.precio:
                cambios.append(f'Precio de {detalle.producto.nombre} cambiado de {precio_anterior} a {detalle.producto.precio}')
            if nombre_anterior != detalle.producto.nombre:
                cambios.append(f'Nombre del producto cambiado de {nombre_anterior} a {detalle.producto.nombre}')

        # Actualizar los datos del usuario asociado a la orden
        orden.usuario.nombre_usuario = request.POST.get('nombre_usuario')
        orden.usuario.nombre_completo = request.POST.get('nombre_completo')
        orden.usuario.rut = request.POST.get('rut')
        orden.usuario.email = request.POST.get('email')
        orden.usuario.telefono = request.POST.get('telefono')
        orden.usuario.direccion = request.POST.get('direccion')
        orden.usuario.save()

        # Recalcular valores de la orden
        subtotal = sum(detalle.cantidad * detalle.producto.precio for detalle in detalles)
        iva = subtotal * 0.19  # Suponiendo un IVA del 19%
        descuento = orden.descuento if orden.descuento else 0
        envio = orden.envio if orden.envio else 0
        total = subtotal + iva - descuento + envio

        # Actualizar la orden
        orden.subtotal = subtotal
        orden.total = total
        orden.save()

        # Actualizar la factura correspondiente
        factura = get_object_or_404(Factura, orden_de_compra=orden)
        factura.subtotal = subtotal
        factura.impuestos = iva
        factura.total = total
        factura.estado = "Por Entregar"
        factura.save()

        return JsonResponse({'success': 'Orden y factura actualizadas exitosamente'})
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def ver_historial(request, orden_id):
    orden = get_object_or_404(OrdenDeCompra, id=orden_id)
    historial = HistorialCambios.objects.filter(orden=orden).order_by('-fecha_cambio')
    return render(request, 'historial.html', {'orden': orden, 'historial': historial})

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
        # Si el usuario es un superusuario, mostramos todas las órdenes
        ordenes = OrdenDeCompra.objects.all().prefetch_related('detalles__producto', 'factura__detalles_estado')
    else:
        try:
            usuario = Usuario.objects.get(nombre_usuario=usuario.nombre_usuario)
        except Usuario.DoesNotExist:
            return HttpResponseForbidden("El usuario no existe.")
        ordenes = OrdenDeCompra.objects.filter(usuario=usuario).prefetch_related('detalles__producto', 'factura__detalles_estado')

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
                'fecha_emision': timezone.now(),
                'estado': 'Por entregar'  # Asignar valor por defecto al crear la factura
            }
        )
        if not created:
            if factura.total != total_factura:
                factura.subtotal = orden.subtotal
                factura.impuestos = impuestos
                factura.total = total_factura
                factura.save()

        # Filtrar facturas para usuarios no superusuarios
        if request.user.is_superuser or factura.estado != 'Entregado':
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

    # Configurar la paginación
    paginator = Paginator(ordenes_con_factura, 1)  # Muestra 2 órdenes por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'lista.html', {'page_obj': page_obj, 'es_superusuario': request.user.is_superuser})

def logout_view(request):
    auth_logout(request)
    return redirect('LOGIN') 

@csrf_exempt
@login_required
def modificar_estado_orden(request, orden_id):
    if request.method == 'POST' and request.user.is_superuser:
        orden = get_object_or_404(OrdenDeCompra, id=orden_id)
        
        if request.content_type == 'application/json':
            # Cuando los datos son enviados como JSON
            data = json.loads(request.body.decode('utf-8'))
        else:
            # Cuando los datos son enviados como form-data (para manejar archivos)
            data = request.POST

        estado = data.get('estado')
        
        if estado:
            if estado == 'Entregado':
                rut = data.get('rut')
                direccion = data.get('direccion')
                foto = request.FILES.get('foto')

                if not rut or not direccion or not foto:
                    return JsonResponse({'error': 'Debe proporcionar RUT, dirección y foto para el estado "Entregado".'}, status=400)
                
                # Guardar los detalles adicionales en la factura
                orden.factura.rut = rut
                orden.factura.direccion = direccion
                orden.factura.foto = foto

                # Asignar "Entregado" como motivo predeterminado
                motivo = "Entregado"
            
            elif estado == 'Rechazado':
                motivo = data.get('motivo')
                if not motivo:
                    return JsonResponse({'error': 'Debe proporcionar un motivo para el estado "Rechazado".'}, status=400)
                
                # Guardar el motivo en la factura
                orden.factura.motivo = motivo
            
            # Crear un nuevo registro en DetalleEstado
            DetalleEstado.objects.create(
                factura=orden.factura,
                estado=estado,
                motivo=motivo  # Guardar el motivo "Entregado" o el proporcionado
            )
            
            # Actualizar el estado de la factura
            orden.factura.estado = estado
            orden.factura.save()

            return JsonResponse({'success': 'Estado de la orden actualizado con éxito.'})
        else:
            return JsonResponse({'error': 'Debe ingresar un estado.'}, status=400)
    return JsonResponse({'error': 'Método no permitido.'}, status=405)

@login_required
def lista_ordenes_facturas(request):
    if request.user.is_superuser:
        ordenes = OrdenDeCompra.objects.all()
    else:
        ordenes = OrdenDeCompra.objects.filter(usuario=request.user)

    ordenes_con_factura = []

    for orden in ordenes:
        factura = Factura.objects.filter(orden_de_compra=orden).first()
        detalles = DetallePedido.objects.filter(orden_de_compra=orden)
        total = sum(detalle.cantidad * detalle.producto.precio for detalle in detalles)
        ordenes_con_factura.append({
            'orden': orden,
            'factura': factura,
            'detalles': detalles,
            'total': total
        })

    return render(request, 'lista.html', {
        'ordenes_con_factura': ordenes_con_factura,
        'es_superusuario': request.user.is_superuser
    })

@csrf_exempt
def modificar_estado(request, orden_id):
    if request.method == 'POST':
        orden = get_object_or_404(OrdenDeCompra, id=orden_id)
        data = json.loads(request.body)
        estado = data.get('estado')
        motivo = data.get('motivo', '')

        factura = orden.factura
        factura.estado = estado
        factura.motivo = motivo
        factura.save()

        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
def lista_facturas_entregadas(request):
    usuario = request.user
    # Filtrar facturas entregadas que pertenecen al usuario actual
    facturas_entregadas = Factura.objects.filter(
        estado='Entregado',
        orden_de_compra__usuario=request.user  # Asumiendo que hay un campo 'usuario' en la orden de compra
    ).prefetch_related('orden_de_compra__detalles__producto')
    
    ordenes = OrdenDeCompra.objects.filter(usuario=usuario).prefetch_related('detalles__producto', 'factura__detalles_estado')
    facturas_con_detalles = []
    for factura in facturas_entregadas:
        detalles_con_totales = [
            {
                'producto': detalle.producto,
                'cantidad': detalle.cantidad,
                'total': detalle.cantidad * detalle.producto.precio
            }
            for detalle in factura.orden_de_compra.detalles.all()
        ]

        facturas_con_detalles.append({
            'factura': factura,
            'orden': factura.orden_de_compra,
            'detalles': detalles_con_totales
        })

    # Configurar la paginación
    paginator = Paginator(facturas_con_detalles, 2)  # Muestra 2 facturas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'facturas_entregadas.html', {'page_obj': page_obj, 'es_superusuario': request.user.is_superuser})

