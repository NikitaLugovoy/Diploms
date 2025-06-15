from django import forms
from .models import TypeDevice

class TypeDeviceForm(forms.ModelForm):
    class Meta:
        model = TypeDevice
        fields = ['name']


