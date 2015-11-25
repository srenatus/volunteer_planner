# coding=utf-8
from django.contrib import admin

from . import forms
from .models import Country, Region, Area, Place


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = (u'id', 'name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ['name']}


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = (u'id', 'name', 'country', 'slug')
    list_filter = ('country',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ['name']}


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    form = forms.AreaAdminForm
    list_display = (u'id', 'region', 'name', 'slug')
    list_filter = ('region',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ['name']}


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    form = forms.PlaceAdminForm

    def get_region(self, obj):
        return obj.area.region
    get_region.short_description = Region._meta.verbose_name

    def get_country(self, obj):
        return self.get_region(obj).country
    get_country.short_description = Country._meta.verbose_name

    list_display = (u'id', 'area', 'get_region', 'get_country', 'name', 'slug')
    list_filter = ('area', 'area__region', 'area__region__country')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ['name']}
