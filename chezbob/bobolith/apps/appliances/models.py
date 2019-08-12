from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class Appliance(models.Model):
    uuid = models.UUIDField(_('appliance uuid'), primary_key=True)
    name = models.CharField(_('appliance name'), max_length=255, unique=True)

    consumer = models.CharField(_('consumer class'), max_length=255)

    STATUS_UP = 'UP'
    STATUS_DOWN = 'DOWN'
    STATUS_UNRESPONSIVE = 'UNRESPONSIVE'

    STATUS_CHOICES = (
        (STATUS_UP, 'Up'),
        (STATUS_DOWN, 'Down'),
        (STATUS_DOWN, 'Unresponsive')
    )

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_DOWN)

    last_connected_at = models.DateTimeField(_('last connected at'), blank=True, null=True)
    last_heartbeat_at = models.DateTimeField(_('last heartbeat at'), blank=True, null=True)

    @property
    def status_icon(self):
        if self.status == Appliance.STATUS_UP:
            return mark_safe('<span style="color: green;">▲</span>')
        if self.status == Appliance.STATUS_UNRESPONSIVE:
            return mark_safe('<span style="color: gold;">▼</span>')
        if self.status == Appliance.STATUS_DOWN:
            return mark_safe('<span style="color: red;">▼</span>')

    status_icon.fget.short_description = _('status')

    def __str__(self):
        return f"{self.name} ({self.uuid})"


class ApplianceLink(models.Model):
    key = models.CharField(_('link key'), max_length=255)

    src_appliance = models.ForeignKey(to=Appliance,
                                      verbose_name=_('source appliance'),
                                      on_delete=models.CASCADE,
                                      related_name='src_links',)

    dst_appliance = models.ForeignKey(to=Appliance,
                                      verbose_name=_('destination appliance'),
                                      on_delete=models.CASCADE,
                                      related_name='dst_links')