from typing import Any
from django import forms
from .models import DCASettings

class DCASettingsCreateForm(forms.ModelForm):
    class Meta:
        model = DCASettings
        exclude = ['user_id', 'running', 'user', 'current_invoke']  # Exclude 'user' field from the form
        # Make 'private_key' field a password field but still populated by defaults
        widgets = {
            'private_key': forms.PasswordInput(render_value=True),
        }
        # Make sure the randomizer value is not negative
        randomizer_value = forms.IntegerField(min_value=0, max_value=99)
        
        

class DCASettingsEditForm(forms.ModelForm):
    class Meta:
        model = DCASettings
        exclude = ['user_id', 'running', 'user', 'current_invoke']  # Exclude 'user' field from the form
        # Make 'private_key' field a password field
        widgets = {
            'private_key': forms.PasswordInput(render_value=True),
        }
        # Make sure the randomizer value is not negative
        randomizer_value = forms.IntegerField(min_value=0, max_value=99)
        
    def __init__(self, *args, **kwargs):
        super(DCASettingsEditForm, self).__init__(*args, **kwargs)
        # If the setting is running, disable the form fields
        if self.instance.running:
            for field in self.fields:
                self.fields[field].disabled = True
                
class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)