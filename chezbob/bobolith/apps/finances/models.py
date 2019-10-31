from collections import deque
from operator import attrgetter

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from djmoney.models import fields as djmoney_fields
from mptt import models as mptt_models
from mptt import utils as mptt_utils

DEBIT = 'debit'
CREDIT = 'credit'


class Account(models.Model):
    ASSET = 'AS'
    EXPENSES = 'EX'
    LIABILITY = 'LI'
    INCOME = 'IN'

    """Debit account balances are increased by debits, decreased by credits (DEAD)."""
    DEBIT_KINDS = {EXPENSES, ASSET}

    """Credit account balances are increased by credits, decreased by debits (CLIC)."""
    CREDIT_KINDS = {LIABILITY, INCOME}

    ACCOUNT_KIND_CHOICES = (
        (ASSET, _('Asset')),
        (EXPENSES, _('Expenses')),
        (LIABILITY, _('Liability')),
        (INCOME, _('Income')),
    )

    name = models.CharField(_('account name'), max_length=255)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete = models.SET_NULL,
        null = True,
        blank = True
    )
    kind = models.CharField(_('account kind'), max_length=2, choices=ACCOUNT_KIND_CHOICES, blank=True)

    @property
    def is_debit_account(self):
        # If an account isn't a credit account (e.g. no kind specified, it's treated as debit).
        return self.kind in Account.DEBIT_KINDS or (self.kind not in Account.CREDIT_KINDS)

    @property
    def is_credit_account(self):
        return self.kind in Account.CREDIT_KINDS

    @property
    def debit_sign(self) -> int:
        if self.is_debit_account:
            return +1
        if self.is_credit_account:
            return -1

    @property
    def credit_sign(self) -> int:
        if self.is_debit_account:
            return -1
        if self.is_credit_account:
            return +1


@receiver(post_save, sender=settings.AUTH_USER_MODEL,
          dispatch_uid="create_user_account")
def create_user_account(sender, instance, created, **kwargs):
    assert sender is settings.AUTH_USER_MODEL
    if created:
        account = Account(kind=Account.LIABILITY,
                          name=f"User {instance.get_username()}",
                          user=instance)
        account.save()


class Transaction(models.Model):
    memo = models.TextField()

    created_at = models.DateTimeField(_('created at'))
    transacted_at = models.DateTimeField(_('transacted at'))
    amount = djmoney_fields.MoneyField(_('amount'),
                                       max_digits=19,
                                       decimal_places=4,
                                       default_currency='USD')

    creditor = models.ForeignKey(
        Account,
        on_delete = models.PROTECT
    )
    debtor = models.ForeignKey(
        Account,
        on_delete = models.PROTECT
    )
