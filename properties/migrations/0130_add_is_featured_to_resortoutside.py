# Generated manually to add missing is_featured field to ResortOutsideIraq

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0129_add_cover_image_to_resortoutside'),
    ]

    operations = [
        migrations.AddField(
            model_name='resortoutsideiraq',
            name='is_featured',
            field=models.BooleanField(default=False, verbose_name='مميز'),
        ),
    ]
