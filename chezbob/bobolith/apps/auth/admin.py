from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from django.utils.translation import gettext_lazy as _

from chezbob.bobolith import admin
from .forms import UserCreationForm
from .models import User, Group


class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'nickname', 'email')}),
        (_('Chez Bob'), {'fields': ('balance', 'last_purchase', 'last_deposit', 'is_fraudulent')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        (_('Personal info'), {
            'classes': ('wide',),
            'fields': ('nickname', 'first_name', 'last_name')
        })
    )

    list_display = ('username', 'email', 'nickname', 'first_name', 'last_name', 'is_staff', 'balance')

    add_form = UserCreationForm

    pass


admin.site.register(User, UserAdmin)


class GroupAdmin(BaseGroupAdmin):
    pass


admin.site.register(Group, GroupAdmin)
