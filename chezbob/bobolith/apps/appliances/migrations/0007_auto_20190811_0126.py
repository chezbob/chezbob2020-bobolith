# Generated by Django 2.2.4 on 2019-08-11 01:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('appliances', '0006_auto_20190811_0125'),
    ]

    operations = [
        migrations.RenameField(
            model_name='appliance',
            old_name='last_heartbeart_at',
            new_name='last_heartbeat_at',
        ),
    ]
