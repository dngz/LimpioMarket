from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', login, name='LOGIN'),
    path('orden_compra/', orden_de_compra, name='orden_de_compra'),
    path('guardar_orden_de_compra/', guardar_orden_de_compra, name='guardar_orden_de_compra'),
    path('login/',login,name='LOGIN'),
    path('lista_productos/', lista_productos, name='lista_productos'),
    path('logout/', logout_view, name='logout'),
    path('visualizar-orden/<int:orden_id>/', visualizar_orden, name='visualizar_orden'),
    path('actualizar-orden/<int:orden_id>/', actualizar_orden, name='actualizar_orden'),
    path('modificar_estado_orden/<int:orden_id>/', modificar_estado_orden, name='mod_es_ord'),
    path('ordenes/<int:orden_id>/modificar_estado/', modificar_estado_orden, name='modificar_estado_orden'),
    path('ordenes/<int:orden_id>/historial/', ver_historial, name='ver_historial'),
    path('facturas_entregadas/', lista_facturas_entregadas, name='facturas_entregadas'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
