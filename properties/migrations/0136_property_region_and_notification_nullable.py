from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0135_alter_buildingrequestsubscription_options_backup'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='region',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='المنطقة'),
        ),
        migrations.AlterField(
            model_name='propertynotification',
            name='property',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='notifications',
                to='properties.property',
                verbose_name='العقار',
            ),
        ),
    ]
