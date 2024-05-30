from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('orden_compra/', orden_de_compra, name='orden_de_compra'),
    path('guardar_orden_de_compra/', guardar_orden_de_compra, name='guardar_orden_de_compra'),
    path('lista_productos/', lista_productos, name='lista_productos'),
]
