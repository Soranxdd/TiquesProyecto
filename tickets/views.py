from datetime import datetime
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView
from django.views.generic.detail import DetailView
from .models import Cliente, Equipo, Ticket, HistorialTicket
from .forms import BuscarClienteForm, ClienteForm, EquipoForm, FolioForm, HistorialForm, TicketCostoForm
from django.utils.timezone import make_aware


# Create your views here.
# Listar tickets, vendedor
class TicketListView(ListView, LoginRequiredMixin):
    model = Ticket
    template_name = 'tickets/vendedor_consultar_tickets.html' # Ruta del template
    context_object_name = 'tickets'
    paginate_by = 10  # Mostrar 10 tickets por página
    
    def dispatch(self, request, *args, **kwargs):
        # Si la sesión expiró, muestra un mensaje y redirige al login
        if not request.user.is_authenticated:
            messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
            return redirect('login')
        
        if not request.user.groups.filter(name='Vendedores').exists():
            # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Técnicos'
            return render(request, '403.html', status=403)

        # Si la sesión es válida, procede normalmente
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtros opcionales
        filtro_fecha = self.request.GET.get('filtroFecha', None)
        filtro_estado = self.request.GET.get('filtroEstado', None)
        filtro_equipo = self.request.GET.get('filtroEquipo', None)

        # Aplicar los filtros si existen
        if filtro_fecha:
            queryset = queryset.filter(fecha_creacion__date=filtro_fecha)
        if filtro_estado:
            queryset = queryset.filter(estado=filtro_estado)
        if filtro_equipo:
            queryset = queryset.filter(equipo__tipo=filtro_equipo)

        return queryset

# Mostrar detalles de un ticket, vendedor
@method_decorator(login_required, name='dispatch')
class TicketDetailView(DetailView):
    model = Ticket
    template_name = 'tickets/vendedor_ticket_detail.html'
    context_object_name = 'ticket'
    
    def dispatch(self, request, *args, **kwargs):
        # Si la sesión expiró, muestra un mensaje y redirige al login
        if not request.user.is_authenticated:
            messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
            return redirect('login')
        
        if request.user.groups.filter(name='Técnicos').exists():
            # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Técnicos'
            return render(request, '403.html', status=403)

        # Si la sesión es válida, procede normalmente
        return super().dispatch(request, *args, **kwargs)

# Asignar tecnico, vendedor
@login_required
def asignar_tecnico(request, ticket_id):
    if not request.user.is_authenticated:
        messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
        return redirect('login')
    # Verificar que el usuario actual es un vendedor
    if request.user.groups.filter(name='Técnicos').exists():
        # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Técnicos'
        return render(request, '403.html', status=403)
    
    # Obtenemos el ticket segun el id del ticket
    ticket = get_object_or_404(Ticket, id=ticket_id)
    # Filtramos los usuarios dentro del grupo técnicos
    tecnicos = User.objects.filter(groups__name='Técnicos')

    # Si el formulario fue enviado (método POST), asignar el técnico al ticket
    if request.method == 'POST':
        # Guardamos el id enviado
        tecnico_id = request.POST.get('tecnico_id')
        # Obtenemos al tecnico segun su id
        tecnico = get_object_or_404(User, id=tecnico_id)
        
        # Guardar el estado anterior solo para el historial
        estado_anterior = ticket.estado 

        ticket.tecnico = tecnico    # Actualizar el técnico asignado
        # ticket.estado = 'diagnostico'   # Cambiar el estado a "diagnostico"
        ticket.save()   #Guardar
        
        # Registrar en el historial
        descripcion = f"Técnico {tecnico.username} asignado al ticket. En espera de que el tecnico revise el equipo y envie el costo inicial estimado."
        HistorialTicket.objects.create(
            ticket=ticket,
            descripcion=descripcion,
            usuario=request.user  # Usuario que realizo el cambio
        )
        
        return redirect('detail', ticket_id)  # Redirigir al detalle del ticket

    return render(request, 'tickets/vendedor_ticket_asignar_tecnico.html', {'ticket': ticket, 'tecnicos': tecnicos})

# No muestra html
@login_required
def marcar_prioridad(request, ticket_id):
    # Obtener el ticket
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Invertir el estado de prioridad
    prioridad_anterior = ticket.prioridad
    ticket.prioridad = not ticket.prioridad  # Cambiar True a False o viceversa
    ticket.save()

    # Registrar en el historial
    descripcion = (
        f"Prioridad del ticket cambiada de {'Alta' if prioridad_anterior else 'Baja'} "
        f"a {'Alta' if ticket.prioridad else 'Baja'}."
    )
    HistorialTicket.objects.create(
        ticket=ticket,
        descripcion=descripcion,
        usuario=request.user  # Usuario que realizó el cambio
    )

    # Redirigir al detalle del ticket o lista
    return redirect('detail', pk=ticket_id)


class BuscarClienteView(View):
    def dispatch(self, request, *args, **kwargs):
        # Si la sesión expiró, muestra un mensaje y redirige al login
        if not request.user.is_authenticated:
            messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
            return redirect('login')
        
        if not request.user.groups.filter(name='Vendedores').exists():
            # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Técnicos'
            return render(request, '403.html', status=403)

        # Si la sesión es válida, procede normalmente
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        form = BuscarClienteForm()
        return render(request, 'tickets/vendedor_buscar_cliente.html', {'form': form})
    
    def post(self, request):
        rut = request.POST.get('rut')  # Capturar el RUT enviado desde el formulario
        cliente = Cliente.objects.filter(rut=rut).first()
        
        if cliente:
            # Si el cliente existe, redirigir al registro del equipo
            return redirect('registrar_equipo', cliente_id=cliente.id)
        else:
            # Si no existe, redirigir al registro del cliente
            return redirect('registrar_cliente')
        
class RegistrarClienteCreateView(CreateView):
    model = Cliente
    template_name = 'tickets/vendedor_registrar_cliente.html'
    form_class = ClienteForm
    success_url = reverse_lazy('buscar_cliente')  # Vuelve al formulario de buscar cliente
    
    def dispatch(self, request, *args, **kwargs):
        # Si la sesión expiró, muestra un mensaje y redirige al login
        if not request.user.is_authenticated:
            messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
            return redirect('login')
        
        if not request.user.groups.filter(name='Vendedores').exists():
            # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Técnicos'
            return render(request, '403.html', status=403)

    def form_valid(self, form):
        # Al guardar, se redirige al registro del equipo
        cliente = form.save()
        return redirect('registrar_equipo', cliente_id=cliente.id)


# Opciones tecnico
@method_decorator(login_required, name='dispatch')
class TicketsAsignadosListView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'tickets/tecnico_tickets.html'
    context_object_name = 'tickets'
    paginate_by = 10
    
    # Para validacion del grupo
    def dispatch(self, request, *args, **kwargs):
        if not request.user.groups.filter(name='Técnicos').exists():
            # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Técnicos'
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # Filtrar los tickets asignados al técnico autenticado
        queryset = Ticket.objects.filter(tecnico=self.request.user)

        # Filtrar por estado si el parámetro está presente en la URL
        estado = self.request.GET.get('estado', 'pendiente')  # Estado por defecto: 'pendiente'
        print(estado)
        queryset = queryset.filter(estado=estado)
        
        # Obtener parámetros del filtro
        fecha = self.request.GET.get('fecha')
        prioridad = self.request.GET.get('prioridad')
        
        if fecha:
            aware_date = make_aware(datetime.strptime(fecha, "%Y-%m-%d"))
            queryset = queryset.filter(fecha_creacion__date=aware_date)
        if prioridad == '1':  # Con prioridad
            queryset = queryset.filter(prioridad=True)
        elif prioridad == '0':  # Sin prioridad
            queryset = queryset.filter(prioridad=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pasar el estado actual al contexto para destacar el botón activo
        context['estado_actual'] = self.request.GET.get('estado', 'pendiente')
        # Pasar la prioridad actual al contexto para mantener el filtro seleccionado
        context['prioridad_actual'] = self.request.GET.get('prioridad', '')
        
        return context
    
@method_decorator(login_required, name='dispatch')
class TecnicoTicketDetailView(DetailView):
    model = Ticket
    template_name = 'tickets/tecnico_ticket_detail.html'
    context_object_name = 'ticket'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
            return redirect('login')
        
        if not request.user.groups.filter(name='Técnicos').exists():
            # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Técnicos'
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

def aceptar_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    # Verifica que el ticket está en estado 'diagnostico'
    if ticket.estado != 'diagnostico':
        return HttpResponseForbidden("Este ticket no puede ser aceptado en su estado actual.")

    # Guardar el estado anterior para registrar en el historial
    estado_anterior = ticket.estado

    # Cambia el estado a 'reparacion'
    ticket.estado = 'reparacion'
    ticket.save()

    # Registrar en el historial
    descripcion = f"Estado del ticket cambiado de {estado_anterior} a {ticket.estado}."
    HistorialTicket.objects.create(
        ticket=ticket,
        descripcion=descripcion,
        usuario=request.user  # Usuario que realizó el cambio
    )

    # Redirige a la lista de tickets asignados
    return redirect('tickets_asignados')

def registrar_avance(request, ticket_id):
    if not request.user.is_authenticated:
        messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
        return redirect('login')
    # Verificar que el usuario actual es un tecnico
    if not request.user.groups.filter(name='Técnicos').exists():
        # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Técnicos'
        return render(request, '403.html', status=403)
    
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Verificar que el ticket está en estado 'reparacion'
    if ticket.estado != 'reparacion':
        return HttpResponseForbidden("Solo se pueden registrar avances en tickets en reparación.")

    if request.method == 'POST':
        form = HistorialForm(request.POST)
        if form.is_valid():
            avance = form.save(commit=False)
            avance.ticket = ticket
            avance.usuario = request.user
            avance.save()
            return redirect('tecnico_detail', pk=ticket_id)  # Cambia según tu vista de detalles
    else:
        form = HistorialForm()

    return render(request, 'tickets/tecnico_registrar_avance.html', {'ticket': ticket, 'form': form})

def marcar_listo(request, ticket_id):
    if not request.user.is_authenticated:
        messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
        return redirect('login')
    # Verificar que el usuario actual es un Tecnico
    if not request.user.groups.filter(name='Técnicos').exists():
        # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Técnicos'
        return render(request, '403.html', status=403)
    
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Verificar que el ticket está en estado 'reparacion'
    if ticket.estado != 'reparacion':
        return HttpResponseForbidden("Solo se pueden marcar como listos los tickets en reparación.")

    if request.method == 'POST':
        form = TicketCostoForm(request.POST, instance=ticket)
        if form.is_valid():
            # Guardar el avance con descripción proporcionada
            descripcion = f"{form.cleaned_data['descripcion_reparacion']}. Costo final: {form.cleaned_data['costo']}"
            # Registrar el cambio en el historial
            HistorialTicket.objects.create(
                ticket=ticket,
                descripcion=descripcion,
                usuario=request.user
            )

            # Cambiar el estado del ticket a 'listo'
            ticket.estado = 'listo'
            ticket.save()

            return redirect('tickets_asignados')  # Cambia según tu vista

    else:
        form = TicketCostoForm(instance=ticket)

    return render(request, 'tickets/tecnico_marcar_listo.html', {'ticket': ticket, 'form': form})

class TecnicoHistorialListView(ListView):
    model = HistorialTicket
    template_name = 'tickets/historial_reparaciones.html'
    context_object_name = 'historial'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
            return redirect('login')
        
        if not request.user.groups.filter(name='Técnicos').exists():
            # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Técnicos'
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        ticket_id = self.kwargs.get('ticket_id')
        print(ticket_id)
        return self.model.objects.filter(ticket_id=ticket_id).order_by('-fecha')
    
def buscar_folio(request):
    if not request.user.is_authenticated:
        messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
        return redirect('login')
    # Verificar que el usuario actual es un vendedor
    if not request.user.groups.filter(name='Técnicos').exists():
        # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Técnicos'
        return render(request, '403.html', status=403)
    
    if request.method == 'POST':
        form = FolioForm(request.POST)
        if form.is_valid():
            folio = form.cleaned_data['folio']
            # Verificar si el folio existe
            equipo = Equipo.objects.filter(folio=folio).first()  # Encuentra el equipo por folio
            if equipo:
                # Buscar el ticket relacionado con el equipo
                ticket = Ticket.objects.filter(equipo=equipo).first()  # Encuentra el primer ticket asociado
                if ticket:
                    # Redirigir al historial del ticket
                    return redirect(reverse('historial_reparaciones', kwargs={'ticket_id': ticket.id}))
                else:
                    # Si no hay tickets asociados
                    form.add_error('folio', 'No hay tickets asociados a este equipo.')
            else:
                # Si el folio no existe
                form.add_error('folio', 'El número de folio no existe.')
    else:
        form = FolioForm()

    return render(request, 'tickets/buscar_folio.html', {'form': form})

class TicketCostoUpdateView(UpdateView):
    template_name = 'tickets/tecnico_ticket_costo.html'
    model = Ticket
    form_class = TicketCostoForm
    success_url = reverse_lazy('tickets_asignados')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
            return redirect('login')
        
        if not request.user.groups.filter(name='Técnicos').exists():
            # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Técnicos'
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        # Obtener el ticket actual y los valores del formulario
        form.instance.estado = 'confirmacion'  # Cambiar el estado a "confirmación"
        form.instance.save()  # Guardar los cambios en la base de datos
        
        nuevo_costo = form.cleaned_data['costo']
        descripcion_reparacion = form.cleaned_data['descripcion_reparacion']

        descripcion = f"Ticket revisado, el precio estimado es: ${nuevo_costo}. Detalles: {descripcion_reparacion}"
        # Registrar el cambio en el historial
        HistorialTicket.objects.create(
            ticket=form.instance,
            descripcion=descripcion,
            usuario=self.request.user
        )
        
        # Actualizar el objeto normalmente
        return super().form_valid(form)
    
def aceptar_precio(request, pk):
    ticket = Ticket.objects.get(pk=pk)
    
    descripcion = f"Precio aceptado por el cliente, se procede a la reparacion del equipo"

    # Guardar el cambio en el historial
    HistorialTicket.objects.create(
        ticket=ticket,
        descripcion=descripcion,
        usuario=request.user
    )

    # Cambiar el estado del ticket
    ticket.estado = 'diagnostico'
    ticket.save()

    # Redirigir al detalle del ticket
    return redirect('detail', pk=ticket.id)

def cancelar_ticket(request, pk):
    ticket = Ticket.objects.get(pk=pk)

    descripcion = f"Ticket cancelado a peticion del cliente."

    # Guardar el cambio en el historial
    HistorialTicket.objects.create(
        ticket=ticket,
        descripcion=descripcion,
        usuario=request.user
    )

    # Cambiar el estado del ticket
    ticket.estado = 'cancelado'
    ticket.save()

    # Redirigir al detalle del ticket
    return redirect('detail', pk=ticket.id)