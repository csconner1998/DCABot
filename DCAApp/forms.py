from django import forms
from .models import InputData

class InputDataForm(forms.ModelForm):
    class Meta:
        model = InputData
        fields = '__all__'  # You can specify fields manually here as a list if needed
