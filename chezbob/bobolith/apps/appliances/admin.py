from django.contrib import admin

from chezbob.bobolith.admin import site as admin_site
from .models import Appliance, ApplianceLink


@admin.register(Appliance, site=admin_site)
class ApplianceAdmin(admin.ModelAdmin):
    list_display = ('name',
                    'uuid',
                    'consumer',
                    'status_icon',
                    'last_connected_at',
                    'last_heartbeat_at')


@admin.register(ApplianceLink, site=admin_site)
class ApplianceLinkAdmin(admin.ModelAdmin):
    pass
