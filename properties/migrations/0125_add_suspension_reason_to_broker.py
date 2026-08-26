# Generated manually to add missing suspension_reason field to Broker

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0124_add_missing_fields_to_resortinside'),
    ]

    operations = [
        migrations.AddField(
            model_name='broker',
            name='suspension_reason',
            field=models.CharField(max_length=200, blank=True, verbose_name='سبب التجميد'),
        ),
    ]
