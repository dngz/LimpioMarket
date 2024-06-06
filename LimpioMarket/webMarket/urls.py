from django.urls import path
from .views import *

urlpatterns = [
    path('', login, name='LOGIN'),
    path('orden_compra/', orden_de_compra, name='orden_de_compra'),
    path('guardar_orden_de_compra/', guardar_orden_de_compra, name='guardar_orden_de_compra'),
    path('login/',login,name='LOGIN'),
    path('lista_productos/', lista_productos, name='lista_productos'),
]
