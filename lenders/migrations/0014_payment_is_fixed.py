# Generated by Django 5.2 on 2025-04-21 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lenders', '0013_paymentemaillog_sentconfirmation'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='is_fixed',
            field=models.BooleanField(default=False, verbose_name='Einmaliger Fixbetrag'),
        ),
    ]
