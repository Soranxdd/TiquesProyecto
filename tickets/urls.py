from django.urls import path
from .views import TicketListView, TicketDetailView, TicketsAsignadosListView, TecnicoTicketDetailView, TecnicoHistorialListView, BuscarClienteView, RegistrarClienteCreateView, TicketCostoUpdateView
from . import views

urlpatterns = [
    path('vendedor/consulta_tickets', TicketListView.as_view(), name='consulta_tickets'),
    path('vendedor/ticket_detail/<int:pk>', TicketDetailView.as_view(), name='detail'),
    path('vendedor/<int:ticket_id>/asignar_tecnico/', views.asignar_tecnico, name='asignar_tecnico'),
    path('tecnico/tickets_asignados/', TicketsAsignadosListView.as_view(), name='tickets_asignados'),
    path('tecnico/ticket_detail/<int:pk>', TecnicoTicketDetailView.as_view(), name='tecnico_detail'),
    path('ticket/<int:pk>/aceptar/', views.aceptar_ticket, name='aceptar_ticket'),
    path('ticket/<int:ticket_id>/registrar_avance/', views.registrar_avance, name='registrar_avance'),
    path('ticket/<int:ticket_id>/listo/', views.marcar_listo, name='marcar_listo'),
    path('ticket/<int:ticket_id>/prioridad/', views.marcar_prioridad, name='marcar_prioridad'),
    path('historial/<int:ticket_id>/', TecnicoHistorialListView.as_view(), name='historial_reparaciones'),
    path('buscar_folio/', views.buscar_folio, name='buscar_folio'),
    path('registrar/', RegistrarClienteCreateView.as_view(), name='registrar_cliente'),
    path('buscar/', BuscarClienteView.as_view(), name='buscar_cliente'),
    path('costo/<int:pk>', TicketCostoUpdateView.as_view(), name='costo'),
    path('ticket/<int:pk>/', TicketDetailView.as_view(), name='ticket_detail'),
    path('ticket/<int:pk>/aceptar_precio/', views.aceptar_precio, name='aceptar_precio'),
    path('ticket/<int:pk>/cancelar_ticket/', views.cancelar_ticket, name='cancelar_ticket'),
]