# Generated manually to add missing cover_image field to ResortInsideIraq

from django.db import migrations, models


def resort_image_path(instance, filename):
    """Generate path for resort images"""
    return f'resorts_inside/{instance.pk}/{filename}'


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0126_add_is_subscription_based_to_property'),
    ]

    operations = [
        migrations.AddField(
            model_name='resortinsideiraq',
            name='cover_image',
            field=models.ImageField(blank=True, upload_to=resort_image_path, verbose_name='صورة الغلاف'),
        ),
    ]
