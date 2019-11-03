from django.contrib import admin
from django.contrib.admin import AdminSite

from .models import Appliance, ApplianceLink


class ApplianceAdmin(admin.ModelAdmin):
    fields = (
        'uuid',
        'name',
        'consumer',
        'status',
        'last_connected_at',
        'last_heartbeat_at'
    )
    readonly_fields = ('uuid',)
    list_display = (
        'name',
        'uuid',
        'consumer',
        'status_icon',
        'last_connected_at',
        'last_heartbeat_at')


class ApplianceLinkAdmin(admin.ModelAdmin):
    pass


def register_default(admin_site: AdminSite):
    admin_site.register(Appliance, ApplianceAdmin)
    admin_site.register(ApplianceLink, ApplianceLinkAdmin)
