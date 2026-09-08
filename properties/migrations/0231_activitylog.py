# Generated migration for ActivityLog model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('properties', '0230_additional_fixes'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('create', 'إنشاء'), ('update', 'تعديل'), ('delete', 'حذف'), ('login', 'تسجيل دخول'), ('logout', 'تسجيل خروج'), ('view', 'عرض'), ('export', 'تصدير'), ('import', 'استيراد'), ('approve', 'موافقة'), ('reject', 'رفض'), ('suspend', 'إيقاف'), ('activate', 'تفعيل'), ('renew', 'تجديد'), ('message', 'رسالة'), ('notification', 'إشعار')], max_length=20, verbose_name='الإجراء')),
                ('model_type', models.CharField(choices=[('broker', 'دلال'), ('property', 'عقار'), ('user', 'مستخدم'), ('subscription', 'اشتراك'), ('office', 'مكتب'), ('system', 'نظام')], max_length=20, verbose_name='نوع النموذج')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True, verbose_name='معرف الكائن')),
                ('object_repr', models.CharField(blank=True, max_length=200, verbose_name='تمثيل الكائن')),
                ('description', models.TextField(blank=True, verbose_name='الوصف')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='عنوان IP')),
                ('user_agent', models.TextField(blank=True, verbose_name='معلومات المتصفح')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='بيانات إضافية')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='التاريخ والوقت')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='activities', to='auth.user', verbose_name='المستخدم')),
            ],
            options={
                'verbose_name': 'سجل النشاط',
                'verbose_name_plural': 'سجلات النشاط',
                'ordering': ['-created_at'],
            },
        ),
    ]