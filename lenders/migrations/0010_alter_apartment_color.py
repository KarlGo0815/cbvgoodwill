# Generated by Django 5.2 on 2025-04-19 17:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lenders', '0009_apartment_color'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apartment',
            name='color',
            field=models.CharField(choices=[('#ff6666', '🍓 Rot'), ('#66b3ff', '🌊 Blau'), ('#99ff99', '🌿 Grün'), ('#ffcc99', '🌅 Orange'), ('#c299ff', '🌸 Lila'), ('#ffff99', '🌞 Gelb'), ('#cccccc', '⚪️ Grau (Standard)')], default='#cccccc', max_length=7, verbose_name='Farbe im Kalender'),
        ),
    ]
