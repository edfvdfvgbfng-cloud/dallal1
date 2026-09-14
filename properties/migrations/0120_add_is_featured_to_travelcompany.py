# Generated manually to add missing is_featured field to TravelCompany

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0119_add_english_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='travelcompany',
            name='is_featured',
            field=models.BooleanField(default=False, verbose_name='مميز'),
        ),
    ]
