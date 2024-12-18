from django.urls import path, include
from .views import RegistrarEquipoCreateView, ObservacionesUpdateView

urlpatterns = [
    path('vendedor/registrar_equipo/<int:cliente_id>/', RegistrarEquipoCreateView.as_view(), name='registrar_equipo'),
    path('vendedor/<int:pk>/modificar_observaciones/', ObservacionesUpdateView.as_view(), name='modificar_observaciones'),
]