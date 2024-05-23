from django.shortcuts import render

def index(request):
    return render(request, 'index.html')  # Asumo que tienes un template llamado 'index.html'
