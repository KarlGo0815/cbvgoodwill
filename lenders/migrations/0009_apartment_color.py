# Generated by Django 5.2 on 2025-04-19 17:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lenders', '0008_booking_override_confirm'),
    ]

    operations = [
        migrations.AddField(
            model_name='apartment',
            name='color',
            field=models.CharField(default='#cccccc', max_length=7, verbose_name='Farbe im Kalender (Hex)'),
        ),
    ]
