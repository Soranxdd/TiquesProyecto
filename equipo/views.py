from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from tickets.forms import EquipoForm, HistorialForm
from tickets.models import Cliente, Equipo, HistorialTicket, Ticket
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# Create your views here.
@method_decorator(login_required, name='dispatch')
class RegistrarEquipoCreateView(CreateView):
    model = Equipo
    template_name = 'equipo/vendedor_registrar_equipo.html'
    form_class = EquipoForm
    success_url = reverse_lazy('consulta_tickets')
    success_message = "¡El equipo ha sido registrado con éxito!"
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar que el cliente exista con el cliente_id de la URL
        self.cliente = get_object_or_404(Cliente, pk=kwargs['cliente_id'])

        if not request.user.is_authenticated:
            messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
            return redirect('login')
        
        if not request.user.groups.filter(name='Vendedores').exists():
            # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Gerente'
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        # Aquí puedes agregar lógica adicional si es necesario
        form.instance.cliente = self.cliente
        form.instance.creado_por = self.request.user  # Por ejemplo, asignar el usuario actual al equipo
        
        # Guardar el equipo para poder usarlo después
        equipo = form.save()
        
        # Buscar el ticket asociado al equipo
        ticket = Ticket.objects.filter(equipo=equipo).first()
        
        descripcion = f"Ticket creado."

        # Guardar el cambio en el historial
        HistorialTicket.objects.create(
            ticket=ticket,
            descripcion=descripcion,
            usuario=self.request.user
        )
        
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class ObservacionesUpdateView(UpdateView):
    model = Equipo
    form_class = HistorialForm
    template_name = 'equipo/vendedor_equipo_modificar_observaciones.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar que el cliente exista con el cliente_id de la URL
        self.cliente = get_object_or_404(Cliente, pk=kwargs['cliente_id'])

        if not request.user.is_authenticated:
            messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
            return redirect('login')
        
        if not request.user.groups.filter(name='Vendedores').exists():
            # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Gerente'
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        # Redirigir al detalle del ticket una vez editadas las observaciones
        ticket_id = self.kwargs['pk']
        return reverse_lazy('detail', kwargs={'pk': ticket_id})

    def get_object(self, queryset=None):
        # Obtener el objeto equipo asociado al id del ticket
        ticket_id = self.kwargs['pk']
        ticket = Ticket.objects.get(id=ticket_id)
        return ticket.equipo