from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Equipo, Ticket

@receiver(post_save, sender=Equipo)
def crear_ticket_al_registrar_equipo(sender, instance, created, **kwargs):
    if created:
        # Crear un ticket automáticamente cuando se registra un nuevo equipo
        Ticket.objects.create(
            equipo=instance,
            vendedor=instance.creado_por,
            estado='pendiente',  # Asegúrate que el campo coincida con el modelo `Ticket`
            descripcion_reparacion='Nuevo equipo registrado'  # Puedes modificar este texto o dejarlo en blanco
        )