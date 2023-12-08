from django import forms
from .models import DCASettings

class DCASettingsCreateForm(forms.ModelForm):
    class Meta:
        model = DCASettings
        exclude = ['user_id', 'running', 'user']  # Exclude 'user' field from the form
        

class DCASettingsEditForm(forms.ModelForm):
    class Meta:
        model = DCASettings
        exclude = ['user_id', 'running', 'user']  # Exclude 'user' field from the form
        
    def __init__(self, *args, **kwargs):
        super(DCASettingsEditForm, self).__init__(*args, **kwargs)
        # If the setting is running, disable the form fields
        if self.instance.running:
            for field in self.fields:
                self.fields[field].disabled = True