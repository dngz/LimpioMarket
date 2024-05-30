from django.shortcuts import render
from django.shortcuts import render, redirect
from .models import Producto, OrdenDeCompra
from django.db.models import F, Sum
from django.http import JsonResponse

def index(request):
    return render(request, 'index.html')  # Asumo que tienes un template llamado 'index.html'

def orden_de_compra(request):
    productos = Producto.objects.all()
    total_precio = productos.aggregate(total=Sum(F('cantidad') * F('precio')))['total'] or 0

    if request.method == 'POST':
        if 'agregar_producto' in request.POST:
            nombre = request.POST['nombre']
            cantidad = int(request.POST['cantidad'])
            precio = float(request.POST['precio'])
            producto = Producto.objects.create(nombre=nombre, cantidad=cantidad, precio=precio)
            return JsonResponse({
                'id': producto.id,
                'nombre': producto.nombre,
                'cantidad': producto.cantidad,
                'precio': producto.precio
            })

    return render(request, 'orden_compra.html', {'productos': productos, 'total_precio': total_precio})

def guardar_orden_de_compra(request):
    if request.method == 'POST':
        direccion = request.POST['direccion']
        correo = request.POST['correo']
        rut = request.POST['rut']
        productos_seleccionados = request.POST.getlist('productos_seleccionados') # Obtener los IDs de los productos seleccionados

        # Validación de la información de contacto
        if not direccion or not correo or not rut:
            return JsonResponse({'error': 'Por favor, complete todos los campos de información de contacto.'})

        # Creación de la orden de compra
        orden_compra = OrdenDeCompra.objects.create(direccion=direccion, correo=correo, rut=rut)
        for producto_id in productos_seleccionados:
            producto = Producto.objects.get(id=producto_id)
            orden_compra.productos.add(producto)
        orden_compra.save()

        # Eliminar los productos añadidos a la orden de compra
        Producto.objects.filter(id__in=productos_seleccionados).delete()

        return JsonResponse({'success': '¡La orden de compra se ha guardado correctamente!'})
    
    return JsonResponse({'error': 'Método no permitido.'})















def lista_productos(request):
    ordenes = OrdenDeCompra.objects.all().prefetch_related('productos')
    return render(request, 'lista.html', {'ordenes': ordenes})