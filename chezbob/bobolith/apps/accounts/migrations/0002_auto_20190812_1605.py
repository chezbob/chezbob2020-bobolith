# Generated by Django 2.2.4 on 2019-08-12 23:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='balance',
        ),
        migrations.RemoveField(
            model_name='user',
            name='last_deposit',
        ),
        migrations.RemoveField(
            model_name='user',
            name='last_purchase',
        ),
    ]