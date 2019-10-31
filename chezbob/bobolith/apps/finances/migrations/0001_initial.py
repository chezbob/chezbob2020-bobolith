# Generated by Django 2.2.4 on 2019-08-13 00:52

from django.db import migrations, models
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='account name')),
                ('code', models.CharField(max_length=5, verbose_name='account code')),
                ('full_code', models.CharField(db_index=True, max_length=255, unique=True, verbose_name='full account code')),
                ('kind', models.CharField(blank=True, choices=[('AS', 'Asset'), ('LI', 'Liability'), ('IN', 'Income'), ('EX', 'Expense'), ('EQ', 'Equity')], max_length=2, verbose_name='account kind')),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='finances.Account')),
            ],
            options={
                'unique_together': {('parent', 'code')},
            },
        ),
    ]