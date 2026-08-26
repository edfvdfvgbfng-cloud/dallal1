# Generated manually to add missing cover_image field to ResortOutsideIraq

from django.db import migrations, models


def resort_image_path(instance, filename):
    """Generate path for resort images"""
    return f'resorts_outside/{instance.pk}/{filename}'


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0128_add_is_featured_to_resortinside'),
    ]

    operations = [
        migrations.AddField(
            model_name='resortoutsideiraq',
            name='cover_image',
            field=models.ImageField(blank=True, upload_to=resort_image_path, verbose_name='صورة الغلاف'),
        ),
    ]
