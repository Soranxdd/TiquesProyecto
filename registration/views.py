from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.utils.timezone import make_aware
from datetime import datetime
from registration.forms import ReportForm
from tickets.models import Report, Ticket
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.messages import get_messages
import re
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages

def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # Inicializar variables de intentos en la sesión
        if 'failed_attempts' not in request.session:
            request.session['failed_attempts'] = 0
            request.session['lockout_until'] = None

        # Verificar si el usuario está bloqueado temporalmente
        lockout_until = request.session.get('lockout_until')
        if lockout_until and timezone.now() < timezone.datetime.fromisoformat(lockout_until):
            tiempo_restante_total = (timezone.datetime.fromisoformat(lockout_until) - timezone.now()).seconds
            minutos = tiempo_restante_total // 60  # Para obtener minutos
            segundos = tiempo_restante_total % 60  # Para obtener segundos
            context = {'error_message': f"Usuario bloqueado. Intenta de nuevo en {minutos} minutos y {segundos} segundos."}
            return render(request, 'registration/login.html', context)

        # Autenticar usuario
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Reiniciar los intentos fallidos si el login es exitoso
            request.session['failed_attempts'] = 0
            request.session['lockout_until'] = None
            login(request, user)
            return redirect('dashboard')
        else:
            # Incrementar intentos fallidos
            request.session['failed_attempts'] += 1

            # Bloquear si supera 3 intentos
            if request.session['failed_attempts'] >= 3:
                request.session['lockout_until'] = (timezone.now() + timedelta(minutes=2)).isoformat()
                context = {'error_message': "Usuario bloqueado temporalmente por intentos fallidos."}
            else:
                context = {'error_message': "Usuario o contraseña incorrectos."}

            return render(request, 'registration/login.html', context)

    return render(request, 'registration/login.html')

def logout_user(request):
    logout(request)
    messages.success(request, 'Sesion terminada')
    return redirect('login')

def logout_time(request):
    logout(request)
    messages.success(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
    return redirect('login')

@method_decorator(login_required, name='dispatch')
class UserListView(ListView):
    model = User
    template_name = 'registration/user_list.html'
    context_object_name = 'users'
    paginate_by = 10
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
            return redirect('login')
        
        if not request.user.groups.filter(name='Gerente').exists():
            # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Gerente'
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # Para obtener el grupo 'Gerente' **cambio**
        gerente_group = Group.objects.get(name='Gerente')
        # Para excluir usuarios que pertenecen al grupo 'Gerente' y superusuarios
        return User.objects.exclude(groups=gerente_group).exclude(is_superuser=True)

def create_user(request):
    storage = get_messages(request)
    for _ in storage:
        pass  # Recorre los mensajes para consumirlos y limpiarlos
    
    if not request.user.is_authenticated:
        messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
        return redirect('login')
        
    if not request.user.groups.filter(name='Gerente').exists():
        # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Gerente'
        return render(request, '403.html', status=403)
    
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        role = request.POST['role']
        
        # Validaciones
        if User.objects.filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya está en uso.")
            return render(request, 'registration/create_user.html', {'roles': ['Técnicos', 'Vendedores']})
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "El correo electrónico ya está en uso.")
            return render(request, 'registration/create_user.html', {'roles': ['Técnicos', 'Vendedores']})
        
        if len(password) < 8:
            messages.error(request, "La contraseña debe tener al menos 8 caracteres.")
            return render(request, 'registration/create_user.html', {'roles': ['Técnicos', 'Vendedores']})

        # Validar si la contraseña contiene una mayúscula, un número y un carácter especial
        if not re.search(r'[A-Z]', password):
            messages.error(request, "La contraseña debe contener al menos una letra mayúscula.")
            return render(request, 'registration/create_user.html', {'roles': ['Técnicos', 'Vendedores']})

        if not re.search(r'\d', password):
            messages.error(request, "La contraseña debe contener al menos un número.")
            return render(request, 'registration/create_user.html', {'roles': ['Técnicos', 'Vendedores']})

        if not re.search(r'[!@#$%^&*(),.?":{}|<>_]', password):  # Puedes agregar más caracteres si es necesario
            messages.error(request, "La contraseña debe contener al menos un carácter especial.")
            return render(request, 'registration/create_user.html', {'roles': ['Técnicos', 'Vendedores']})
        
        if role not in ['Técnicos', 'Vendedores']:
            messages.error(request, "Seleccione un rol válido.")
            return render(request, 'registration/create_user.html', {'roles': ['Técnicos', 'Vendedores']})
        
        # Crear usuario
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Asignar al grupo
        group = Group.objects.get(name=role)
        user.groups.add(group)
        
        messages.success(request, "Usuario creado exitosamente.")
        return redirect('user_list')
    
    return render(request, 'registration/create_user.html', {'roles': ['Técnicos', 'Vendedores']})

def edit_user(request, user_id):
    storage = get_messages(request)
    for _ in storage:
        pass  # Recorre los mensajes para consumirlos y limpiarlos
    
    if not request.user.is_authenticated:
        messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
        return redirect('login')
        
    if not request.user.groups.filter(name='Gerente').exists():
        # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Gerente'
        return render(request, '403.html', status=403)
    
    user = User.objects.get(id=user_id)
    if request.method == 'POST':
        user.username = request.POST['username']
        user.email = request.POST['email']
        role = request.POST['role']
        
        # Validaciones
        if User.objects.filter(username=request.POST['username']).exclude(id=user.id).exists():
            messages.error(request, "El nombre de usuario ya está en uso.")
            return render(request, 'registration/edit_user.html', {'user': user, 'roles': ['Técnicos', 'Vendedores']})
        
        if User.objects.filter(email=request.POST['email']).exclude(id=user.id).exists():
            messages.error(request, "El correo electrónico ya está en uso.")
            return render(request, 'registration/edit_user.html', {'user': user, 'roles': ['Técnicos', 'Vendedores']})
        
        if role not in ['Técnicos', 'Vendedores']:
            messages.error(request, "Seleccione un rol válido.")
            return render(request, 'registration/edit_user.html', {'user': user, 'roles': ['Técnicos', 'Vendedores']})
        
        # Actualizar grupo
        user.groups.clear()  # Para eliminar grupos anteriores
        group = Group.objects.get(name=role)
        user.groups.add(group)
        
        user.save()
        return redirect('user_list')
    
    return render(request, 'registration/edit_user.html', {'user': user, 'roles': ['Técnicos', 'Vendedores']})

def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, f'Usuario {user.username} eliminado con éxito.')
    return redirect('user_list')

@method_decorator(login_required, name='dispatch')
class GerenteTicketListView(ListView):
    model = Ticket
    template_name = 'registration/gerente_ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 10
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
            return redirect('login')
        
        if not request.user.groups.filter(name='Gerente').exists():
            # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Gerente'
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # Base query
        queryset = Ticket.objects.all()

        # Obtener parámetros del filtro
        tecnico_id = self.request.GET.get('tecnico')
        vendedor_id = self.request.GET.get('vendedor')
        estado = self.request.GET.get('estado')
        fecha = self.request.GET.get('fecha')

        # El filtrado si se envio un parametro
        if tecnico_id:
            queryset = queryset.filter(tecnico_id=tecnico_id)
        if vendedor_id:
            queryset = queryset.filter(vendedor_id=vendedor_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        if fecha:
            aware_date = make_aware(datetime.strptime(fecha, "%Y-%m-%d"))
            queryset = queryset.filter(fecha_creacion__date=aware_date)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Añadir datos necesarios para los filtros
        context['tecnicos'] = User.objects.filter(groups__name='Técnicos')
        context['vendedores'] = User.objects.filter(groups__name='Vendedores')
        context['estados'] = Ticket.status_ticket  # Enum de estados en el modelo Ticket
        return context

@method_decorator(login_required, name='dispatch')    
class ReportListView(ListView):
    model = Report
    template_name = 'registration/gerente_report_list.html'
    context_object_name = 'reports'
    paginate_by = 10
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
            return redirect('login')
        
        if not request.user.groups.filter(name='Gerente').exists():
            # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Gerente'
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # Base query
        queryset = Report.objects.all()

        # Obtener parámetros del filtro
        fecha_inicio = self.request.GET.get('fecha_inicio')
        fecha_fin = self.request.GET.get('fecha_fin')
        tipo_reporte = self.request.GET.get('tipo_reporte')

        # El filtrado si se envio un parametro
        if fecha_inicio and fecha_fin:
            queryset = queryset.filter(
                fecha_inicio__gte=fecha_inicio,
                fecha_fin__lte=fecha_fin
            )
            
        if tipo_reporte:
            if tipo_reporte == 'tecnico':
                queryset = queryset.filter(tecnico__isnull=False)
            elif tipo_reporte == 'vendedor':
                queryset = queryset.filter(vendedor__isnull=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Pasar valores actuales de los filtros al contexto para mantenerlos en el formulario
        context['fecha_inicio'] = self.request.GET.get('fecha_inicio', '')
        context['fecha_fin'] = self.request.GET.get('fecha_fin', '')
        context['tipo_reporte'] = self.request.GET.get('tipo_reporte', '')
        return context

@method_decorator(login_required, name='dispatch')    
class ReportCreateView(CreateView):
    model = Report
    form_class = ReportForm
    template_name = 'registration/gerente_report_create.html'
    success_url = reverse_lazy('reports_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
            return redirect('login')
        
        if not request.user.groups.filter(name='Gerente').exists():
            # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Gerente'
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Obtener datos del formulario
        usuario = form.cleaned_data['usuario']

        # Guardar el reporte sin necesidad de asociar tickets
        reporte = form.save(commit=False)
        reporte.usuario = usuario  # Asegura que el reporte esté asociado al usuario
        reporte.save()

        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')    
class ReportDetailView(DetailView):
    model = Report
    template_name = 'registration/gerente_report_detail.html'
    context_object_name = 'report'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.")
            return redirect('login')
        
        if not request.user.groups.filter(name='Gerente').exists():
            # Devuelve HTTP 403 Forbidden si el usuario no pertenece al grupo 'Gerente'
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.get_object()
        if report.usuario.groups.filter(name='Técnicos').exists():
            context['rendimiento'] = report.calcular_rendimiento_tecnico()
        elif report.usuario.groups.filter(name='Vendedores').exists():
            context['rendimiento'] = report.calcular_rendimiento_vendedor()
        return context