from django import forms
from .models import Body

class BodyForm(forms.ModelForm):
    class Meta:
        model = Body
        fields = ['number', 'address']
