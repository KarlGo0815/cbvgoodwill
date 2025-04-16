# Generated by Django 5.2 on 2025-04-16 11:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lenders', '0004_apartment_booking'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='custom_total_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='Pauschalpreis (optional)'),
        ),
        migrations.CreateModel(
            name='SeasonalRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('price_per_night', models.DecimalField(decimal_places=2, max_digits=7)),
                ('apartment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seasonal_rates', to='lenders.apartment')),
            ],
        ),
    ]
