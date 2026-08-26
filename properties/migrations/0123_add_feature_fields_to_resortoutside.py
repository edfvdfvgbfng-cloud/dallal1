# Generated manually to add missing feature fields to ResortOutsideIraq

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0122_add_capacity_fields_to_resortoutside'),
    ]

    operations = [
        migrations.AddField(
            model_name='resortoutsideiraq',
            name='has_restaurant',
            field=models.BooleanField(default=False, verbose_name='مطعم'),
        ),
        migrations.AddField(
            model_name='resortoutsideiraq',
            name='has_cafe',
            field=models.BooleanField(default=False, verbose_name='مقهى'),
        ),
        migrations.AddField(
            model_name='resortoutsideiraq',
            name='has_spa',
            field=models.BooleanField(default=False, verbose_name='سبا'),
        ),
        migrations.AddField(
            model_name='resortoutsideiraq',
            name='has_gym',
            field=models.BooleanField(default=False, verbose_name='نادي رياضي'),
        ),
        migrations.AddField(
            model_name='resortoutsideiraq',
            name='has_conference_hall',
            field=models.BooleanField(default=False, verbose_name='قاعة مؤتمرات'),
        ),
    ]
