from django import forms
from .models import Cliente, Equipo, HistorialTicket, Ticket
from django.core.exceptions import ValidationError

class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = ['tipo', 'marca', 'otra_marca', 'observaciones', 'incluye_cargador']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'marca': forms.Select(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'incluye_cargador': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        
    def clean_marca(self):
        # Validar que la marca no esté vacía y tenga un mínimo de caracteres
        marca = self.cleaned_data.get('marca')
        print(marca)
        if not marca:
            raise ValidationError("El campo 'Marca' no puede estar vacío.")
        if len(marca) < 2:
            raise ValidationError("La marca debe tener al menos 2 caracteres.")
        return marca

    def clean_observaciones(self):
        # Validar que las observaciones tengan al menos 10 caracteres
        observaciones = self.cleaned_data.get('observaciones')
        print(observaciones)
        if not observaciones:
            raise ValidationError("El campo 'Observaciones' no puede estar vacío.")
        if len(observaciones) < 6:
            raise ValidationError("Las observaciones deben tener al menos 6 caracteres.")
        return observaciones

    def clean(self):
        # Validación general (dependencias entre campos)
        cleaned_data = super().clean()
        marca = cleaned_data.get('marca')
        otra_marca = cleaned_data.get('otra_marca')
            
        if marca == 'otra' and not otra_marca:
            self.add_error('otra_marca', 'Debe especificar la marca si selecciona "Otra".')
        
        return cleaned_data
        
class HistorialForm(forms.ModelForm):
    class Meta:
        model = HistorialTicket
        fields = ['descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe el avance realizado...'}),
        }
        
class FolioForm(forms.Form):
    folio = forms.CharField(label='Ingrese el número de folio', max_length=100, required=True)
    
class BuscarClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['rut']
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control','label': 'RUT del Cliente' , 'placeholder': 'Ingrese el RUT del cliente'}),
        }
    
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['rut', 'nombre', 'correo', 'telefono']
        
class TicketCostoForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['descripcion_reparacion', 'costo']
        widgets = {
            'descripcion_reparacion': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Ingrese la descripcion.'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el costo.'})
        }

    def clean_descripcion_reparacion(self):
        # Validar que las observaciones tengan al menos 10 caracteres
        descripcion = self.cleaned_data.get('descripcion_reparacion')
        if not descripcion:
            raise ValidationError("El campo 'Descripcion' no puede estar vacío.")
        if len(descripcion) < 6:
            raise ValidationError("La descripcion deben tener al menos 6 caracteres.")
        return descripcion
        
    def clean_costo(self):
        costo = self.cleaned_data.get('costo')
        if costo < 0:
            raise ValidationError('El costo no puede ser negativo.')
        if costo == 0:
            raise ValidationError('El costo no puede ser 0.')
        if costo > 1000000000:
            raise ValidationError('El costo no puede superar los 1.000.000.000 CLP.')
        return costo