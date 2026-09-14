# Generated manually to add missing district field to ResortOutsideIraq

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0120_add_is_featured_to_travelcompany'),
    ]

    operations = [
        migrations.AddField(
            model_name='resortoutsideiraq',
            name='district',
            field=models.CharField(blank=True, max_length=100, verbose_name='المنطقة'),
        ),
    ]
