from django.shortcuts import render, redirect
from .models import Producto, OrdenDeCompra
from django.db.models import F, Sum
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.messages import get_messages
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json

def index(request):
    return render(request, 'index.html')

@login_required
def orden_de_compra(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso para acceder a esta página")

    productos = Producto.objects.all()
    total_precio = productos.aggregate(total=Sum(F('precio')))['total'] or 0

    if request.method == 'POST':
        if 'agregar_producto' in request.POST:
            nombre = request.POST['nombre']
            precio = float(request.POST['precio'])
            producto = Producto.objects.create(nombre=nombre, precio=precio)
            return JsonResponse({
                'id': producto.id,
                'nombre': producto.nombre,
                'precio': producto.precio
            })

    return render(request, 'orden_compra.html', {'productos': productos, 'total_precio': total_precio})

@login_required
def guardar_orden_de_compra(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso para acceder a esta página")

    if request.method == 'POST':
        direccion = request.POST['direccion']
        correo = request.POST['correo']
        rut = request.POST['rut']
        productos_seleccionados = request.POST.getlist('productos_seleccionados')

        if not direccion or not correo or not rut:
            return JsonResponse({'error': 'Por favor, complete todos los campos de información de contacto.'})

        orden_compra = OrdenDeCompra.objects.create(usuario=request.user, direccion=direccion, correo=correo, rut=rut)
        
        # Correctamente agregar productos a la orden de compra
        for producto_id in productos_seleccionados:
            producto = Producto.objects.get(id=producto_id)
            orden_compra.productos.add(producto)

        orden_compra.save()

        Producto.objects.filter(id__in=productos_seleccionados).delete()

        return JsonResponse({'success': '¡La orden de compra se ha guardado correctamente!'})
    
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
    if not request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso para acceder a esta página")
    
    ordenes = OrdenDeCompra.objects.all().prefetch_related('productos')
    ordenes_con_total = []

    for orden in ordenes:
        total = orden.productos.aggregate(total=Sum(F('cantidad') * F('precio')))['total'] or 0
        ordenes_con_total.append({
            'orden': orden,
            'total': total,
        })
    
    return render(request, 'lista.html', {'ordenes_con_total': ordenes_con_total})
