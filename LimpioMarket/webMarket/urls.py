from django.urls import path
from .views import index

urlpatterns = [
    path('', index, name='index'),  # Asumo que 'index' es la vista de la página principal
]
