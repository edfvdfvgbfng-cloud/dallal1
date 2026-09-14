# Generated manually to add missing fields to ResortInsideIraq

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0123_add_feature_fields_to_resortoutside'),
    ]

    operations = [
        migrations.AddField(
            model_name='resortinsideiraq',
            name='district',
            field=models.CharField(max_length=100, verbose_name='المنطقة'),
        ),
        migrations.AddField(
            model_name='resortinsideiraq',
            name='total_rooms',
            field=models.IntegerField(default=0, verbose_name='إجمالي الغرف'),
        ),
        migrations.AddField(
            model_name='resortinsideiraq',
            name='total_chalets',
            field=models.IntegerField(default=0, verbose_name='إجمالي الشاليهات'),
        ),
        migrations.AddField(
            model_name='resortinsideiraq',
            name='max_capacity',
            field=models.IntegerField(default=0, verbose_name='السعة القصوى'),
        ),
        migrations.AddField(
            model_name='resortinsideiraq',
            name='has_restaurant',
            field=models.BooleanField(default=False, verbose_name='مطعم'),
        ),
        migrations.AddField(
            model_name='resortinsideiraq',
            name='has_cafe',
            field=models.BooleanField(default=False, verbose_name='مقهى'),
        ),
        migrations.AddField(
            model_name='resortinsideiraq',
            name='has_spa',
            field=models.BooleanField(default=False, verbose_name='سبا'),
        ),
        migrations.AddField(
            model_name='resortinsideiraq',
            name='has_gym',
            field=models.BooleanField(default=False, verbose_name='نادي رياضي'),
        ),
        migrations.AddField(
            model_name='resortinsideiraq',
            name='has_conference_hall',
            field=models.BooleanField(default=False, verbose_name='قاعة مؤتمرات'),
        ),
    ]
