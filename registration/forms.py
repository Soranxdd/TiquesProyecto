from django import forms
from django.contrib.auth.models import User, Group
from tickets.models import Report


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['usuario', 'fecha_inicio', 'fecha_fin']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtramos solo técnicos y vendedores en el campo usuario
        self.fields['usuario'].queryset = User.objects.filter(
            groups__name__in=['Técnicos', 'Vendedores']
        )
        self.fields['usuario'].label = "Seleccionar Técnico/Vendedor"