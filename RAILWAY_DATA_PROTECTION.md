# حماية البيانات على Railway - إرشادات للحفاظ على البيانات

## المشكلة
عند النشر على Railway باستخدام Git، قد يتم فقدان البيانات المخزنة في قاعدة البيانات PostgreSQL إذا لم يتم تكوين النظام بشكل صحيح.

## الحل

### 1. فصل البيانات عن الكود
قاعدة بيانات PostgreSQL على Railway هي **service منفصل** عن الكود. هذا يعني:
- البيانات محفوظة في PostgreSQL service
- الكود يتم نشره في service آخر
- إعادة نشر الكود لا يجب أن تؤثر على البيانات

### 2. التكوين الحالي (صحيح)

#### railway.toml
```toml
[variables]
ALLOW_SQLITE_FALLBACK = "False"
```
هذا يمنع استخدام SQLite في الإنتاج.

#### Dockerfile
```dockerfile
ENV ALLOW_SQLITE_FALLBACK=False
ENV DATABASE_PROTECTION_ENABLED=True
```
هذا يضمن حماية قاعدة البيانات.

#### run_server.py
```python
# CRITICAL: Using --noinput to prevent any destructive operations
run([sys.executable, 'manage.py', 'migrate', '--noinput'], allow_fail=True)
```
هذا يطبق الـ migrations فقط بدون حذف البيانات.

### 3. التأكد من أن PostgreSQL محفوظة

#### الخطوة 1: تحقق من Railway Dashboard
1. افتح Railway Dashboard
2. انتقل إلى المشروع
3. تأكد من وجود **PostgreSQL service** منفصل
4. تأكد من أن **DATABASE_URL** في متغيرات البيئة يشير إلى PostgreSQL service

#### الخطوة 2: تحقق من متغيرات البيئة
في Railway Dashboard، تأكد من وجود:
```
DATABASE_URL=postgres://...
```
وليس:
```
DATABASE_URL=sqlite://...
```

### 4. ما الذي يجب فعله وما الذي يجب تجنبه

#### ✅ ما يجب فعله
- استخدام `migrate --noinput` (موجود في run_server.py)
- استخدام `collectstatic --noinput` (موجود في run_server.py)
- الحفاظ على PostgreSQL service منفصل
- عمل backup دوري للبيانات

#### ❌ ما يجب تجنبه
- **لا تستخدم** `flush` أو `reset` في الإنتاج
- **لا تستخدم** `makemigrations` في الإنتاج
- **لا تستخدم** `createsuperuser` في الإنتاج (استخدم Django admin)
- **لا تحذف** PostgreSQL service
- **لا تغير** DATABASE_URL في Railway

### 5. عملية النشر الآمنة

#### عند النشر الجديد:
```bash
# 1. عمل backup قبل النشر
python manage.py dbbackup

# 2. نشر الكود فقط
git add .
git commit -m "Update code"
git push

# 3. Railway سيقوم تلقائياً بـ:
# - بناء Docker image
# - تشغيل migrate --noinput (آمن)
# - تشغيل collectstatic --noinput
# - إعادة تشغيل server
# البيانات محفوظة في PostgreSQL service
```

### 6. ما الذي قد يسبب فقدان البيانات؟

#### ❌ قد يسبب فقدان البيانات:
1. حذف PostgreSQL service من Railway
2. تغيير DATABASE_URL إلى قاعدة بيانات جديدة
3. استخدام `flush` أو `reset` في الإنتاج
4. إضافة migrations جديدة تحذف البيانات (например، `RunPython` مع حذف)

#### ✅ لن يسبب فقدان البيانات:
1. تغيير الكود في views.py
2. تغيير HTML templates
3. تغيير CSS/JS
4. إضافة migrations جديدة (إذا كانت آمنة)
5. إعادة نشر الكود

### 7. التحقق من سلامة البيانات

#### قبل النشر:
```bash
# عد البيانات الحالية
python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.count())"
python manage.py shell -c "from properties.models import Property; print(Property.objects.count())"
```

#### بعد النشر:
```bash
# تحقق من أن البيانات موجودة
python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.count())"
python manage.py shell -c "from properties.models import Property; print(Property.objects.count())"
```

### 8. استعادة البيانات (إذا حدث خطأ)

#### من Railway Backup:
1. افتح Railway Dashboard
2. انتقل إلى PostgreSQL service
3. ابحث عن "Backups" أو "Snapshots"
4. اختر النسخة الاحتياطية قبل النشر
5. انقر "Restore"

#### من Django Backup:
```bash
# إذا كنت تستخدم django-dbbackup
python manage.py dbrestore --backup=<backup-file>
```

### 9. إعداد Backup تلقائي

#### إضافة إلى railway.toml:
```toml
[variables]
BACKUP_ENABLED = "True"
BACKUP_SCHEDULE = "0 2 * * *"  # يومياً الساعة 2 صباحاً
BACKUP_RETENTION_DAYS = "30"
```

#### أو استخدام Railway Cron:
1. افتح Railway Dashboard
2. أضف **Cron service**
3. أضف command:
```bash
python manage.py dbbackup
```

### 10. اختبار الإعداد

#### اختبار محلي:
```bash
# 1. تأكد من أن PostgreSQL يعمل
python manage.py check --database default

# 2. تأكد من أن migrations آمنة
python manage.py migrate --plan

# 3. اختبار migrate (سيظهر فقط ما سيتم تطبيقه)
python manage.py migrate --dry-run
```

#### اختبار على Railway:
1. نشر على Railway
2. تحقق من أن البيانات موجودة
3. تحقق من logs (يجب أن يظهر "migrate --noinput")

### 11. قائمة التحقق قبل النشر

قبل كل نشر، تأكد من:
- [ ] PostgreSQL service موجود ويعمل
- [ ] DATABASE_URL يشير إلى PostgreSQL
- [ ] لا يوجد `flush` أو `reset` في الكود
- [ ] `migrate --noinput` مستخدم في run_server.py
- [ ] backup تم عمله مؤخراً
- [ ] `ALLOW_SQLITE_FALLBACK=False` في متغيرات البيئة

### 12. استكشاف الأخطاء

#### إذا كانت البيانات مفقودة بعد النشر:
1. تحقق من Railway Dashboard - هل PostgreSQL service لا يزال موجوداً؟
2. تحقق من متغيرات البيئة - هل DATABASE_URL صحيح؟
3. تحقق من logs - هل ظهرت أخطاء في migrate؟
4. استرجع من backup

#### إذا ظهرت أخطاء في migrate:
1. تحقق من أن migrations آمنة
2. استخدم `migrate --plan` لمعرفة ما سيتم تطبيقه
3. إذا كانت migration خطيرة، احذفها محلياً وأعد النشر

### 13. نصائح إضافية

#### الحفاظ على migrations:
- **لا تحذف** migrations من git
- **لا تستخدم** `--fake` في الإنتاج
- دائماً استخدم `makemigrations` محلياً قبل النشر

#### الحفاظ على البيانات:
- قم بعمل backup قبل أي تغيير كبير
- استخدم transactions في الكود
- اختبر الكود محلياً أولاً

#### مراقبة:
- راقب Railway logs بعد كل نشر
- راقب database size في Railway Dashboard
- راقب errors في Sentry (إذا كان موجوداً)

---

## الخلاصة

النظام الحالي في المشروع **محمي بشكل صحيح** بواسطة:
1. `ALLOW_SQLITE_FALLBACK=False` في railway.toml
2. `DATABASE_PROTECTION_ENABLED=True` في Dockerfile
3. `migrate --noinput` في run_server.py
4. PostgreSQL service منفصل على Railway

**مهم:** البيانات محفوظة في PostgreSQL service المنفصل، وليس في الكود. إعادة نشر الكود لن تؤثر على البيانات إذا تم اتباع الإرشادات أعلاه.

إذا كنت مازال تواجه مشكلة فقدان البيانات، تأكد من:
1. أن PostgreSQL service لا يتم حذفه أو إعادة إنشائه
2. أن DATABASE_URL لا يتغير
3. أنك لا تستخدم `flush` أو `reset` في الإنتاج
