from collections import deque
from operator import attrgetter

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from djmoney.models import fields as djmoney_fields
from mptt import models as mptt_models
from mptt import utils as mptt_utils

DEBIT = 'debit'
CREDIT = 'credit'


class Account(mptt_models.MPTTModel):
    ASSET = 'AS'
    EXPENSES = 'EX'
    DRAWING = 'DR'
    LIABILITY = 'LI'
    INCOME = 'IN'
    CAPITAL = 'CA'

    """Debit account balances are increased by debits, decreased by credits (DEAD)."""
    DEBIT_KINDS = {EXPENSES, ASSET, DRAWING}

    """Credit account balances are increased by credits, decreased by debits (CLIC)."""
    CREDIT_KINDS = {LIABILITY, INCOME, CAPITAL}

    ACCOUNT_KIND_CHOICES = (
        (ASSET, _('Asset')),
        (EXPENSES, _('Expenses')),
        (DRAWING, _('Drawing')),
        (LIABILITY, _('Liability')),
        (INCOME, _('Income')),
        (CAPITAL, _('Capital')),
    )

    name = models.CharField(_('account name'), max_length=255)
    parent = mptt_models.TreeForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        db_index=True,
        on_delete=models.CASCADE
    )

    code = models.CharField(_('account code'), max_length=5)

    full_code = models.CharField(_('full account code'), max_length=255, db_index=True, unique=True)

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

    @property
    def computed_full_code(self):
        """
        The full code of this account, computed from the database.

        This is triggered on an account and all descendents when its code changes,
        and therefore full_code == computed_full_code should always be True.
        """

        # Normally, we would use values_list for this, but here we assume that
        # this method has been called after get_cached_trees, so we can skip the db.
        # In the worst case, this results in a lot of queries (like it would anyways).

        ancestor_codes = map(attrgetter('code'), self.get_ancestors(include_self=True))
        return "-".join(ancestor_codes)

    def __str__(self):
        return f"{self.full_code} – {self.name}"

    class MPTTMeta:
        order_insertion_by = ["code"]

    class Meta:
        unique_together = (("parent", "code"),)


@receiver(post_save, sender=Account, dispatch_uid="maintain_integrity_account_full_code")
def maintain_integrity_account_full_code(sender, instance: Account, update_fields=None, **kwargs):
    assert sender is Account
    if kwargs.get('raw', False):
        return

    if update_fields is None or 'code' in update_fields:
        # WARNING: YOU ARE NOW ENTERING THE QUERY OPTIMIZATION ZONE.
        # Avoid extra queries on get_children/get_ancestors by caching the entire subtree.

        descendants = instance.get_descendants(include_self=True)
        [cached_root] = mptt_utils.get_cached_trees(descendants)  # type: Account

        # To avoid an N+1 query problem, stage our changes, and then bulk update in one go.
        # We use a deque rather than recursion to avoid Python's recursion limit.

        stale_accounts = deque([cached_root])
        dirty_accounts = list()

        while stale_accounts:
            account = stale_accounts.popleft()
            account.full_code = account.computed_full_code
            dirty_accounts.append(account)

            for child in account.get_children():
                stale_accounts.append(child)

        Account.objects.bulk_update(dirty_accounts, ['full_code'])


class Transaction(models.Model):
    memo = models.TextField()

    created_at = models.DateTimeField(_('created at'))
    transacted_at = models.DateTimeField(_('transacted at'))

    # This field is maintained by signals. Do not modify it directly.
    accounts = models.ManyToManyField(Account, related_name='transactions')


class TransactionLeg(models.Model):
    KIND_CHOICES = (
        (DEBIT, _('Debit')),
        (CREDIT, _('Credit'))
    )

    transaction = models.ForeignKey(Transaction,
                                    related_name='legs',
                                    on_delete=models.CASCADE)

    account = models.ForeignKey(Account,
                                related_name="transaction_legs",
                                on_delete=models.CASCADE)

    amount = djmoney_fields.MoneyField(_('amount'),
                                       max_digits=19,
                                       decimal_places=4,
                                       default_currency='USD')

    kind = models.CharField(_('kind'),
                            max_length=15,
                            choices=KIND_CHOICES,
                            help_text="Is this transaction leg a debit or credit?")

    memo = models.TextField(default="", blank=True)

    @property
    def sign(self):
        if self.kind == DEBIT:
            return self.account.debit_sign
        if self.kind == CREDIT:
            return self.account.credit_sign

    @property
    def signed_amount(self):
        return self.sign * self.amount

    def __str__(self):
        return f"{self.account.name} {self.signed_amount}"


@receiver(post_save, sender=TransactionLeg, dispatch_uid="maintain_integrity_transaction_accounts")
def maintain_integrity_transaction_accounts(sender, instance: TransactionLeg, update_fields=None, **kwargs):
    """
    When a transaction leg is saved, update the transaction it is a part of to include
    the account in its `accounts` list.
    """

    assert sender is TransactionLeg
    if kwargs.get('raw', False):
        return

    if not update_fields or 'account' in update_fields:
        transaction = instance.transaction
        transaction.accounts.set(transaction.legs.values_list('account', flat=True))
        transaction.save()
