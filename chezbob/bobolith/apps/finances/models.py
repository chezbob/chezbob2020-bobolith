from operator import attrgetter

from django.db import models, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from mptt import models as mptt_models
from mptt import utils as mptt_utils

DEBIT = 'debit'
CREDIT = 'credit'


class Account(mptt_models.MPTTModel):
    ASSET = 'AS'
    LIABILITY = 'LI'
    INCOME = 'IN'
    EXPENSE = 'EX'
    EQUITY = 'EQ'

    ACCOUNT_KIND_CHOICES = (
        (ASSET, 'Asset'),
        (LIABILITY, 'Liability'),
        (INCOME, 'Income'),
        (EXPENSE, 'Expense'),
        (EQUITY, 'Equity')
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


@receiver(post_save, sender=Account, dispatch_uid="maintain_integrity_full_code")
def maintain_integrity_full_code(sender, instance: Account, update_fields=None, **kwargs):
    print(f"UPDATE_FIELDS: {update_fields}")

    assert sender is Account
    if kwargs.get('raw', False):
        return

    if update_fields is None or 'code' in update_fields:
        # WARNING: YOU ARE NOW ENTERING THE 3AM QUERY OPTIMIZATION ZONE

        # Avoid queries on get_children/get_ancestors by caching the entire subtree.

        descendants = instance.get_descendants(include_self=True)
        [cached_account_tree] = mptt_utils.get_cached_trees(descendants)  # type: Account

        # By default, Django auto-commits, meaning it will hit the database once for
        # each call to save. By updating full_code's in a transaction, we reduce that
        # to a single hit.

        # But we go even further by staging our changes, and then bulk updating in one go.

        with transaction.atomic():
            dirty_accounts = []

            def recursive_update(account: Account):
                account.full_code = account.computed_full_code
                dirty_accounts.append(account)

                for child_account in account.get_children():
                    recursive_update(child_account)

            recursive_update(cached_account_tree)
            Account.objects.bulk_update(dirty_accounts, ['full_code'])
