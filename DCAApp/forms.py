from django import forms
from .models import DCASettings

class DCASettingsForm(forms.ModelForm):
    class Meta:
        model = DCASettings
        exclude = ['user_id', 'running', 'user']  # Exclude 'user' field from the form

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(DCASettingsForm, self).__init__(*args, **kwargs)

        if self.user:
            user_settings = DCASettings.objects.filter(user=self.user).first()
            if user_settings:
                for field_name in self.fields:
                    self.fields[field_name].initial = getattr(user_settings, field_name)
                    self.fields[field_name].disabled = user_settings.running
    def save(self, commit=True):
        if self.user and self.instance:
            for field_name in self.fields:
                setattr(self.instance, field_name, self.cleaned_data.get(field_name))
            self.instance.user = self.user  # Set the instance user here
            self.instance.save()
            return self.instance
        else:
            instance = super(DCASettingsForm, self).save(commit=False)
            if self.user:
                instance.user = self.user
                instance.save()
            return instance if commit else None
