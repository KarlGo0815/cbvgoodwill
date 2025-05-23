# Generated by Django 5.2 on 2025-04-13 17:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lenders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Loan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loan_type', models.CharField(choices=[('flexible', 'Flexibles Darlehen'), ('fixed', 'Festes Darlehen')], max_length=10)),
                ('target_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Zielbetrag (nur bei festen Darlehen)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('lender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loans', to='lenders.lender')),
            ],
        ),
    ]
