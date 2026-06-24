from django import forms
from .models import Paciente

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            'ci', 'nombres', 'apellidos', 'fecha_nacimiento', 
            'sexo', 'peso', 'talla', 'telefono_tutor', 'nombre_tutor'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'ci': forms.TextInput(attrs={'class': 'form-control'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'sexo': forms.Select(choices=[('M', 'Masculino'), ('F', 'Femenino')], attrs={'class': 'form-control'}),
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'talla': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'telefono_tutor': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_tutor': forms.TextInput(attrs={'class': 'form-control'}),
        }
