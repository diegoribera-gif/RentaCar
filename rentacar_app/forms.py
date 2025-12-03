from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import Cliente, Vehiculo, Reserva, Empleado

class UserForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['cedula_identidad', 'telefono', 'direccion', 'licencia_conducir', 'fecha_vencimiento_licencia']
        widgets = {
            'fecha_vencimiento_licencia': forms.DateInput(attrs={'type': 'date'}),
            'direccion': forms.Textarea(attrs={'rows': 3}),
        }

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = '__all__'
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'fecha_adquisicion': forms.DateInput(attrs={'type': 'date'}),
        }

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['cliente', 'vehiculo', 'fecha_inicio', 'fecha_fin', 'observaciones']
        widgets = {
            'fecha_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_fin': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.filter(
            fecha_vencimiento_licencia__gte=timezone.now().date()
        )
        self.fields['vehiculo'].queryset = Vehiculo.objects.filter(estado='DISPONIBLE')
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        vehiculo = cleaned_data.get('vehiculo')
        
        if fecha_inicio and fecha_fin:
            if fecha_inicio >= fecha_fin:
                raise forms.ValidationError("La fecha de fin debe ser posterior a la fecha de inicio")
            
            if vehiculo:
                reservas_conflictivas = Reserva.objects.filter(
                    vehiculo=vehiculo,
                    fecha_inicio__lte=fecha_fin,
                    fecha_fin__gte=fecha_inicio,
                    estado__in=['CONFIRMADA', 'ACTIVA', 'PENDIENTE']
                ).exclude(pk=self.instance.pk if self.instance else None)
                
                if reservas_conflictivas.exists():
                    raise forms.ValidationError(
                        f"El vehículo no está disponible en las fechas seleccionadas."
                    )
        
        return cleaned_data

class EmpleadoUserForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = ['telefono', 'direccion']
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3}),
        }