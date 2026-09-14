# دليل سريع - حماية البيانات على Railway

## المشكلة
عند النشر على Railway، البيانات قد تُفقد إذا لم يتم تكوين النظام بشكل صحيح.

## الحل السريع

### 1. تشغيل سكريبت التحقق
```bash
python scripts/verify_railway_setup.py
```

هذا السكريبت سيتحقق من:
- ✅ استخدام PostgreSQL (وليس SQLite)
- ✅ DATABASE_URL صحيح
- ✅ ALLOW_SQLITE_FALLBACK = False
- ✅ DEBUG = False
- ✅ الاتصال بقاعدة البيانات
- ✅ .gitignore يحتوي على ملفات SQLite

### 2. قبل النشر
```bash
# 1. تأكد من أن التحقق ينجح
python scripts/verify_railway_setup.py

# 2. عد البيانات الحالية
python manage.py shell -c "from django.contrib.auth.models import User; print('Users:', User.objects.count())"
python manage.py shell -c "from properties.models import Property; print('Properties:', Property.objects.count())"

# 3. نشر الكود
git add .
git commit -m "Update code"
git push
```

### 3. بعد النشر
```bash
# تحقق من أن البيانات موجودة
python manage.py shell -c "from django.contrib.auth.models import User; print('Users:', User.objects.count())"
python manage.py shell -c "from properties.models import Property; print('Properties:', Property.objects.count())"
```

### 4. إذا كانت البيانات مفقودة

#### الخيار 1: استعادة من Railway Backup
1. افتح Railway Dashboard
2. انتقل إلى PostgreSQL service
3. ابحث عن "Backups"
4. اختر النسخة قبل النشر
5. انقر "Restore"

#### الخيار 2: استعادة من Django Backup
```bash
python manage.py dbrestore --backup=<backup-file>
```

## النقاط الأساسية

### ✅ ما يجب فعله
- ✅ استخدام `migrate --noinput` (موجود في run_server.py)
- ✅ استخدام `collectstatic --noinput` (موجود في run_server.py)
- ✅ الحفاظ على PostgreSQL service منفصل
- ✅ تعيين `ALLOW_SQLITE_FALLBACK=False`
- ✅ تعيين `DEBUG=False`

### ❌ ما يجب تجنبه
- ❌ استخدام `flush` أو `reset`
- ❌ استخدام `makemigrations` في الإنتاج
- ❌ حذف PostgreSQL service
- ❌ تغيير DATABASE_URL
- ❌ تعيين `ALLOW_SQLITE_FALLBACK=True`

## التكوين الحالي (صحيح)

المشروع يحتوي على الحماية التالية:

### railway.toml
```toml
[variables]
ALLOW_SQLITE_FALLBACK = "False"
```

### Dockerfile
```dockerfile
ENV ALLOW_SQLITE_FALLBACK=False
ENV DATABASE_PROTECTION_ENABLED=True
```

### run_server.py
```python
run([sys.executable, 'manage.py', 'migrate', '--noinput'], allow_fail=True)
```

### .gitignore
```
db.sqlite3
*.sqlite3
muq.sqlite3
```

## استكشاف الأخطاء

### إذا فشل السكريبت:
1. تحقق من Railway Dashboard
2. تأكد من وجود PostgreSQL service
3. تأكد من DATABASE_URL في متغيرات البيئة
4. راجع `RAILWAY_DATA_PROTECTION.md` للمزيد من التفاصيل

### إذا كانت البيانات مفقودة:
1. تحقق من Railway Dashboard - هل PostgreSQL service موجود؟
2. تحقق من متغيرات البيئة - هل DATABASE_URL صحيح؟
3. استرجع من backup

## المزيد من المعلومات

- راجع `RAILWAY_DATA_PROTECTION.md` للتفاصيل الكاملة
- راجع `FINAL_RELEASE_REPORT.md` للتقرير الشامل
- راجع `.env.example` للمتغيرات المطلوبة

---

**مهم:** البيانات محفوظة في PostgreSQL service المنفصل، وليس في الكود. إعادة نشر الكود لن تؤثر على البيانات إذا تم اتباع الإرشادات أعلاه.
