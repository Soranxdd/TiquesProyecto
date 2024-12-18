from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from tickets.models import Ticket
from django.contrib.auth.models import User

# Create your views here.
def dashboard(request):
    # Para verificar a que grupo pertenece el usuario
    if request.user.groups.filter(name='Gerente').exists():
        tickets_pendientes = Ticket.objects.filter(estado='pendiente').count()
        tickets_listos = Ticket.objects.filter(estado='listo').count()
        tickets_totales = Ticket.objects.all().count()

        # Técnicos y vendedores activos
        tecnicos_totales = User.objects.filter(groups__name='Técnicos', tickets_asignados__isnull=False).distinct().count()
        vendedores_totales = User.objects.filter(groups__name='Vendedores', equipos_creados__isnull=False).distinct().count()

        context = {
            'tickets_pendientes': tickets_pendientes,
            'tickets_listos': tickets_listos,
            'tickets_totales': tickets_totales,
            'tecnicos_activos': tecnicos_totales,
            'vendedores_activos': vendedores_totales,
        }
        
        return render(request, 'dashboard/opciones_gerente.html', context)  # Redirigir a la vista del gerente
    
    elif request.user.groups.filter(name='Vendedores').exists():
        tickets_pendientes = Ticket.objects.filter(vendedor=request.user.id, estado='pendiente').count()
        tickets_listos = Ticket.objects.filter(vendedor=request.user.id, estado='listo').count()
        tickets_totales = Ticket.objects.all().count()

        context = {
            'tickets_pendientes': tickets_pendientes,
            'tickets_listos': tickets_listos,
            'tickets_totales': tickets_totales,
        }
        
        return render(request, 'dashboard/opciones_vendedor.html', context)  # Redirigir a la vista del vendedor
    
    elif request.user.groups.filter(name='Técnicos').exists():
        tickets_pendientes = Ticket.objects.filter(tecnico=request.user.id, estado='pendiente').count()
        tickets_listos = Ticket.objects.filter(tecnico=request.user.id, estado='listo').count()
        tickets_totales = Ticket.objects.all().count()

        context = {
            'tickets_pendientes': tickets_pendientes,
            'tickets_listos': tickets_listos,
            'tickets_totales': tickets_totales,
        }
        
        return render(request, 'dashboard/opciones_tecnico.html', context)  # Redirigir a la vista del tecnico