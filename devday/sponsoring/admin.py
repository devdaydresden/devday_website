from django import forms
from django.contrib import admin
from ordered_model.admin import OrderedTabularInline

from sponsoring.models import SponsoringPackageItem, SponsoringPackage


class SponsoringPackageItemForm(forms.ModelForm):
    class Meta:
        widgets = {'description': forms.Textarea(attrs={'rows': 1}), }


class SponsoringPackageItemTabularInline(OrderedTabularInline):
    model = SponsoringPackageItem
    fields = (
        'name', 'description', 'is_header', 'order', 'move_up_down_links',)
    readonly_fields = ('order', 'move_up_down_links',)
    extra = 1
    ordering = ('order',)
    form = SponsoringPackageItemForm


@admin.register(SponsoringPackage)
class SponsoringPackageAdmin(admin.ModelAdmin):
    list_display = ('package_type', 'event', 'pricing',)
    list_filter = ('event',)
    inlines = (SponsoringPackageItemTabularInline,)
