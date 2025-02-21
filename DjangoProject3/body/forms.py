from django import forms
from .models import Body

class BodyForm(forms.ModelForm):
    class Meta:
        model = Body
        fields = ['number', 'address']


from django import forms

class ScheduleForm(forms.Form):
    name = forms.CharField(max_length=255, label="Название расписания")
    office = forms.IntegerField(label="ID Офиса")
    datetime_start = forms.DateTimeField(label="Дата и время начала")
    datetime_end = forms.DateTimeField(label="Дата и время окончания")
