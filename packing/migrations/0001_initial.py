# Generated by Django 5.2.1 on 2025-07-01 07:37

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('client', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NetWeight',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('part_no', models.CharField(max_length=100)),
                ('net_wt', models.DecimalField(decimal_places=3, max_digits=10)),
                ('count', models.PositiveIntegerField(default=1)),
            ],
            options={
                'unique_together': {('part_no', 'net_wt')},
            },
        ),
        migrations.CreateModel(
            name='PackingDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('part_no', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('hsn_no', models.CharField(blank=True, max_length=20, null=True)),
                ('gst', models.CharField(blank=True, null=True)),
                ('brand_name', models.CharField(blank=True, max_length=100, null=True)),
                ('total_packing_qty', models.IntegerField(blank=True, null=True)),
                ('mrp_invoice', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('mrp_box', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('total_mrp', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('npr', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('nsr', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('packed_in_plastic_bag', models.IntegerField(blank=True, null=True)),
                ('case_no_start', models.IntegerField(blank=True, null=True)),
                ('case_no_end', models.IntegerField(blank=True, null=True)),
                ('total_case', models.IntegerField(blank=True, null=True)),
                ('net_wt', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('gross_wt', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('total_net_wt', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('total_gross_wt', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('length', models.IntegerField(blank=True, null=True)),
                ('width', models.IntegerField(blank=True, null=True)),
                ('height', models.IntegerField(blank=True, null=True)),
                ('cbm', models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='packings', to='client.client')),
            ],
        ),
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('part_no', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('description', models.TextField()),
                ('qty', models.IntegerField()),
                ('brand_name', models.CharField(max_length=100)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_items', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Packing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('part_no', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('qty', models.IntegerField()),
                ('stock_qty', models.IntegerField()),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.client')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('client', 'part_no'), name='unique_client_partno')],
            },
        ),
    ]
