# Generated manually to add missing is_featured field to ResortInsideIraq

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0127_add_cover_image_to_resortinside'),
    ]

    operations = [
        migrations.AddField(
            model_name='resortinsideiraq',
            name='is_featured',
            field=models.BooleanField(default=False, verbose_name='مميز'),
        ),
    ]
