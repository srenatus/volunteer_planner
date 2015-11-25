from django import forms 
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.contrib import admin

from .models import Country, Region, Area, Place



# http://stackoverflow.com/a/32111885/993018
def add_related_field_wrapper(form, col_name):
    rel_model = form.Meta.model
    rel = rel_model._meta.get_field(col_name).rel
    form.fields[col_name].widget = RelatedFieldWidgetWrapper(form.fields[col_name].widget, rel, admin.site, can_add_related=True, can_change_related=True)


class OrderedModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.ordering_name


class PlaceAdminForm(forms.ModelForm):
    area = OrderedModelChoiceField(queryset=Area.objects)

    class Meta:
        model = Place
        fields = ('name', 'slug', 'area')
        # XXX new in django 1.9
        # field_classes = {
        #     'area': OrderedModelChoiceField,
        # }

    def __init__(self, *args, **kwargs):
        super(PlaceAdminForm, self).__init__(*args, **kwargs)
        add_related_field_wrapper(self, 'area')


class AreaAdminForm(forms.ModelForm):
    region = OrderedModelChoiceField(queryset=Region.objects)

    class Meta:
        model = Area
        fields = ('name', 'slug', 'region')

    def __init__(self, *args, **kwargs):
        super(AreaAdminForm, self).__init__(*args, **kwargs)
        add_related_field_wrapper(self, 'region')
