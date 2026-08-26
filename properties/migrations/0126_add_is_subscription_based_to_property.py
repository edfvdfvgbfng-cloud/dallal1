# Generated manually to add missing is_subscription_based field to Property

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0125_add_suspension_reason_to_broker'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='is_subscription_based',
            field=models.BooleanField(default=False, verbose_name='مبني على الاشتراك'),
        ),
    ]
