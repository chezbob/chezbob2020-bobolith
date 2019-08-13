from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from chezbob.bobolith.admin import site as admin_site
from .models import Account


@admin.register(Account, site=admin_site)
class AccountAdmin(MPTTModelAdmin):
    list_display = ('full_code', 'name', 'kind')

    fields = ('name', 'parent', 'code', 'kind')
    readonly_fields = ('full_code',)