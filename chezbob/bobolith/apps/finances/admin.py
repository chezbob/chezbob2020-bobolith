from django import forms
from django.contrib import admin
from djmoney.forms import MoneyWidget
from moneyed import USD
from mptt.admin import MPTTModelAdmin

from chezbob.bobolith.admin import site as admin_site
from chezbob.bobolith.apps.finances import models
from .models import Account, Transaction, TransactionLeg


class AccountTransactionInlineAdmin(admin.TabularInline):
    model = Transaction.accounts.through
    extra = 0

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class TransactionLegAdminForm(forms.ModelForm):
    class Meta:
        model = TransactionLeg
        widgets = {
            'amount': MoneyWidget(currency_widget=forms.Select(choices=[(USD, '$')])),
        }
        fields = '__all__'


class TransactionLegInlineAdmin(admin.TabularInline):
    model = TransactionLeg
    form = TransactionLegAdminForm
    extra = 0


@admin.register(Account, site=admin_site)
class AccountAdmin(MPTTModelAdmin):
    fields = ('name', 'parent', 'code', 'kind')
    readonly_fields = ('full_code',)

    list_display = ('name', 'full_code', 'kind')

    inlines = (AccountTransactionInlineAdmin,)


@admin.register(Transaction, site=admin_site)
class TransactionAdmin(admin.ModelAdmin):
    fields = ('created_at', 'transacted_at', 'memo')

    list_display = ('memo', 'debit_summary', 'credit_summary', 'created_at', 'transacted_at')

    inlines = (TransactionLegInlineAdmin,)

    @staticmethod
    def debit_summary(tx: Transaction):
        debit_legs = tx.legs.filter(kind=models.DEBIT).select_related('account')

        summary = []
        for leg in debit_legs:
            summary.append(f"{leg.account.name} {leg.account.debit_sign * leg.amount}")

        return ", ".join(summary)

    @staticmethod
    def credit_summary(tx: Transaction):
        credit_legs = tx.legs.filter(kind=models.CREDIT).select_related('account')

        summary = []
        for leg in credit_legs:
            summary.append(f"{leg.account.name} {leg.account.credit_sign * leg.amount}")

        return ", ".join(summary)
