# Railway Variables Setup Guide
## دليل إعداد Railway Variables لمشروع دلال

### ⚠️ حرج: الحاوية تفشل الآن بسبب Railway Variables مفقودة

السجلات الحالية تظهر:
```
DATABASE_URL exists: NO
SECRET_KEY exists: NO
DEBUG=
```

بسبب إصلاحات الأمان الأخيرة:
- DEBUG فارغ يُعامل كـ production
- Production يفشل بدون DATABASE_URL
- Production يفشل بدون SECRET_KEY

### 🔧 خطوات الإعداد في Railway Dashboard

#### 1. افتح Railway Dashboard
- انتقل إلى: https://railway.app
- اختر project: dallal1
- اختر service: dallal1 (Django app)

#### 2. أضف Railway Variables

**أ) DATABASE_URL (حرج جداً)**
- انقر على "Variables"
- انقر "New Variable"
- Name: `DATABASE_URL`
- Value: `{{Postgres.DATABASE_URL}}`
  - **مهم:** هذا Reference Variable، ليس كلمة مرور حقيقية
  - Railway سيستبدل هذا تلقائياً بـ PostgreSQL connection string
  - تأكد أن PostgreSQL service مرتبط بـ dallal1 service

**ب) SECRET_KEY (حرج جداً)**
- انقر "New Variable"
- Name: `SECRET_KEY`
- Value: (generate strong secret)
  - استخدم هذا الأمر لتوليد:
    ```bash
    python -c "import secrets; print(secrets.token_urlsafe(50))"
    ```
  - مثال: `xy9ZpK4mN8qR7tL2wX5vB6cD3eF9gH1jK4mN8pQ7rS3tU6vW2xY5zA8cD1eF4gH7j`
  - **مهم:** احفظ هذا secret في مكان آمن
  - **مهم:** لا تشاركه مع أحد

**ج) DEBUG (مهم)**
- انقر "New Variable"
- Name: `DEBUG`
- Value: `False`
  - يجب أن يكون `False` (مع حرف F كبيرة)
  - لا تتركه فارغاً

**د) ALLOWED_HOSTS (اختياري)**
- انقر "New Variable"
- Name: `ALLOWED_HOSTS`
- Value: `*`
  - أو استخدم: `muqq.up.railway.app,dallal1-production.up.railway.app`

#### 3. تأكد من PostgreSQL Service

**أ) فحص Postgres Service**
- في Railway dashboard، اختر PostgreSQL service
- تأكد أنه مرتبط بـ dallal1 service
- انقر "Settings" → "Reference Variables"
- تأكد أن `DATABASE_URL` معرف

**ب) فحص Volume**
- انقر "Storage"
- تأكد أن Volume ID موجود
- سجل Volume ID للمرجع

**ج) فحص Backups**
- انقر "Backups"
- تأكد أن pgbackrest يعمل
- تأكد وجود backups حديثة

#### 4. إعادة البناء

بعد إضافة Variables:
- Railway سيقوم بإعادة بناء تلقائياً
- أو انقر "Redeploy" يدوياً
- انتظر 1-2 دقيقة للبناء

#### 5. فحص السجلات

بعد إعادة البناء:
- انقر "Logs"
- تأكد من:
  ```
  DATABASE_URL exists: YES
  SECRET_KEY exists: YES
  DEBUG=False
  ```
- تأكد أن التطبيق لا يفشل عند بدء التشغيل

### 🎯 بعد إعداد Railway Variables

بعد إضافة Variables وحل migrations:

#### 1. حل Migrations Conflict

المشكلة الحالية:
```
relation "properties_property_slug_f3b16024_like" already exists
```

الخيارات:

**أ) حل في Railway PostgreSQL Console**
- انقر PostgreSQL service
- انقر "Console"
- شغل:
  ```sql
  DROP INDEX IF EXISTS properties_property_slug_f3b16024_like;
  ```
- ثم أزل التخطي من entrypoint.sh

**ب) Fake Migration إذا Schema مطابق**
- إذا Database schema مطابق مع migration 0004
- شغل في Railway console:
  ```bash
  python manage.py migrate properties 0003 --fake
  python manage.py migrate properties
  ```

**ج) إعادة إنشاء Database إذا فارغة**
- إذا Database فارغة (لا توجد بيانات)
- احذف PostgreSQL service
- أنشئ PostgreSQL جديد
- شغل migrations كاملة

#### 2. إزالة Migrations Skip

في entrypoint.sh:
```bash
# القديم:
echo "Skipping migrations for now due to database conflicts..."

# الجديد:
echo "Running migrations..."
python manage.py migrate --noinput
```

#### 3. اختبار التطبيق

بعد كل شيء:
- افتح: https://muqq.up.railway.app/
- تأكد من:
  - CSS و JS يعملان
  - Database tables موجودة
  - Filtering options تعمل
  - Counters تعمل

### 📋 ملخص Railway Variables المطلوبة

| Variable | Value | Required | Note |
|----------|-------|----------|------|
| DATABASE_URL | {{Postgres.DATABASE_URL}} | ✅ Yes | Reference Variable |
| SECRET_KEY | (generate strong secret) | ✅ Yes | 50+ chars random |
| DEBUG | False | ✅ Yes | Case-sensitive |
| ALLOWED_HOSTS | * | ⚠️ Optional | Or specific domains |

### ⚠️ قواعد ذهبية

1. **لا تقم بأي شيء قبل إضافة Railway Variables**
   - الحاوية ستفشل بدونها
   - هذا سلوك صحيح للأمان

2. **لا تحذف PostgreSQL service بدون فحص Backups**
   - قد توجد بيانات Production
   - تأكد من وجود backups أولاً

3. **لا تعمل migrations بدون حل conflict**
   - الحاوية ستفشل عند migration
   - حل conflict أولاً

4. **لا تعتبر المشروع جاهزاً للإنتاج حتى:**
   - Railway Variables معرفة
   - PostgreSQL Volume مؤكد
   - Migrations تعمل
   - Static files تعمل
   - Filtering options تعمل

### 🆘 المشاكل الشائعة

**سؤال:** لماذا الحاوية تتوقف بعد 5 ثواني؟
**جواب:** Railway يوقف الحاوية لأن التطبيق يفشل في Production mode (DATABASE_URL مفقود). بعد إضافة Variables، سيعمل.

**سؤال:** لماذا CSS/JS لا تعمل؟
**جواب:** WhiteNoise يحتاج staticfiles في staticfiles/. collectstatic يعمل لكن container يتوقف قبل أن يخدم static files. بعد إضافة Variables، سيعمل.

**سؤال:** لماذا Database error؟
**جواب:** Migrations مخطاة مؤقتاً. بعد حل conflict وإزالة التخطي، ستعمل.

### 📞 إذا واجهت مشاكل

1. شفر Railway logs أولاً
2. شفر هذا guide أولاً
3. شفر RAILWAY_PRODUCTION_SAFETY_REPORT.md
4. تأكد من Railway Variables
5. تأكد من PostgreSQL connection
6. شفر السجلات لمزيد من المساعدة