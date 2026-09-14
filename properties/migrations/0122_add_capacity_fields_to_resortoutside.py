# Generated manually to add missing capacity fields to ResortOutsideIraq

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0121_add_district_to_resortoutside'),
    ]

    operations = [
        migrations.AddField(
            model_name='resortoutsideiraq',
            name='total_rooms',
            field=models.IntegerField(default=0, verbose_name='إجمالي الغرف'),
        ),
        migrations.AddField(
            model_name='resortoutsideiraq',
            name='total_chalets',
            field=models.IntegerField(default=0, verbose_name='إجمالي الشاليهات'),
        ),
        migrations.AddField(
            model_name='resortoutsideiraq',
            name='max_capacity',
            field=models.IntegerField(default=0, verbose_name='السعة القصوى'),
        ),
    ]
