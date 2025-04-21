from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ("lenders", "0016_sentconfirmation_booking"),
    ]

    operations = [
        migrations.AddField(
            model_name='sentconfirmation',
            name='booking',
            field=models.ForeignKey(
                to='lenders.booking',
                on_delete=django.db.models.deletion.CASCADE,
                null=True,
                blank=True,
            ),
        ),
    ]
