# إعداد متغيرات البيئة في Railway

## المشكلة الحالية
التطبيق يفشل في البدء بسبب عدم وجود متغيرات البيئة المطلوبة:
- `DATABASE_URL` - مطلوب للاتصال بقاعدة بيانات PostgreSQL
- `SECRET_KEY` - مطلوب لأمان Django

## الحل السريع - خطوة بخطوة

### 1. إضافة خدمة PostgreSQL

1. اذهب إلى لوحة تحكم Railway لمشروعك
2. اضغط على **"New Service"**
3. اختر **"Database"**
4. اختر **"PostgreSQL"**
5. اضغط **"Add PostgreSQL"**

### 2. إضافة متغيرات البيئة المطلوبة

1. في لوحة تحكم Railway، اذهب إلى خدمة Django الخاصة بك
2. اضغط على تبويب **"Variables"**
3. أضف المتغيرات التالية:

#### المتغيرات المطلوبة (الحد الأدنى):

```
DATABASE_URL = ${{Postgres.DATABASE_URL}}
SECRET_KEY = <your-secret-key-here>
DEBUG = False
ALLOWED_HOSTS = muqq.up.railway.app
```

**ملاحظة مهمة:** بالنسبة لـ `DATABASE_URL`، استخدم الصيغة التالية في Railway:
- في حقل الاسم: `DATABASE_URL`
- في حقل القيمة: `${{Postgres.DATABASE_URL}}`
- هذا سيقوم Railway تلقائياً بربط متغير البيئة بخدمة PostgreSQL

#### لتوليد SECRET_KEY:

في الكمبيوتر المحلي، قم بتشغيل:
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```
انسخ الناتج واستخدمه كقيمة لـ `SECRET_KEY`

### 3. إعادة النشر

بعد إضافة المتغيرات:
1. Railway سيقوم تلقائياً بإعادة نشر التطبيق
2. انتظر اكتمال النشر (عادة 2-5 دقائق)
3. تحقق من السجلات للتأكد من نجاح النشر

## متغيرات البيئة الإضافية (اختياري)

يمكنك إضافة هذه المتغيرات لتحسين الوظائف:

```
# OAuth للدخول عبر Google (اختياري)
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = <your-google-client-id>
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = <your-google-client-secret>

# Email (اختياري)
EMAIL_HOST = smtp.gmail.com
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = <your-email>
EMAIL_HOST_PASSWORD = <your-email-password>

# Maps API (اختياري)
GOOGLE_MAPS_API_KEY = <your-google-maps-api-key>
```

## التحقق من النشر

بعد إضافة المتغيرات:
1. راقب السجلات في Railway
2. يجب أن ترى رسالة نجاح مثل:
   ```
   === Starting Django Application on Railway ===
   DATABASE_URL exists: YES
   SECRET_KEY exists: YES
   === PRODUCTION MODE ===
   Running Django migrations...
   Starting Django on port 8000...
   ```

3. افتح النطاق العام: `https://muqq.up.railway.app`

## استكشاف الأخطاء

### إذا فشل النشر:

1. **تحقق من وجود خدمة PostgreSQL:**
   - تأكد من أن خدمة PostgreSQL موجودة وتعمل
   - تحقق من أن متغير `DATABASE_URL` يستخدم `${{Postgres.DATABASE_URL}}`

2. **تحقق من متغيرات البيئة:**
   - تأكد من أن `SECRET_KEY` تم تعيينه بقيمة صالحة (50+ حرف)
   - تأكد من أن `DEBUG` = `False`
   - تأكد من أن `ALLOWED_HOSTS` يحتوي على النطاق العام

3. **تحقق من السجلات:**
   - راقب سجلات Railway للتأكد من عدم وجود أخطاء

### إذا استمرت المشكلة:

1. قم بإعادة تشغيل خدمة Django في Railway
2. إذا فشل، قم بإعادة بناء (Rebuild) الخدمة
3. إذا فشل، قم بإزالة وإعادة إضافة خدمة PostgreSQL

## الدعم

للمزيد من المعلومات:
- `RAILWAY_DEPLOYMENT_GUIDE.md` - دليل شامل للنشر
- `RAILWAY_VARIABLES_SETUP_GUIDE.md` - دليل تفصيلي لمتغيرات البيئة