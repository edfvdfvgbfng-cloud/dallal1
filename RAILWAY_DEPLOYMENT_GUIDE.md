# دليل نشر دلال على Railway

هذا الدليل الشامل يساعدك على نشر منصة دلال على Railway من البداية إلى النهاية.

## 📋 المتطلبات الأساسية

- حساب GitHub
- حساب Railway (https://railway.app)
- مستودع GitHub يحتوي على المشروع
- المعرفة الأساسية باستخدام Git

## 🚀 خطوات النشر

### 1. إعداد المستودع على GitHub

1. **تأكد من وجود ملفات النشر المطلوبة:**
   - `railway.toml` - تكوين Railway
   - `Dockerfile` - إعداد الحاوية
   - `requirements.txt` - المكتبات المطلوبة
   - `runtime.txt` - إصدار Python
   - `Procfile` - أمر بدء التشغيل
   - `entrypoint.sh` - سكريبت البدء
   - `start.sh` - سكريبت بدء Railway

2. **ادفع الكود إلى GitHub:**
```bash
git add .
git commit -m "تحضير للنشر على Railway"
git push origin main
```

### 2. إنشاء مشروع على Railway

1. **تسجيل الدخول إلى Railway:**
   - افتح https://railway.app
   - سجل الدخول باستخدام GitHub

2. **إنشاء مشروع جديد:**
   - اضغط على "New Project"
   - اختر "Deploy from GitHub repo"
   - حدد مستودع المشروع من قائمة GitHub
   - اضغط على "Deploy Now"

### 3. إضافة خدمة PostgreSQL

1. **إضافة قاعدة البيانات:**
   - في لوحة تحكم Railway، اضغط على "New Service"
   - اختر "Database"
   - اختر "PostgreSQL"
   - Railway سيقوم بإنشاء قاعدة بيانات وإضافة `DATABASE_URL` تلقائياً

2. **ربط قاعدة البيانات بالمشروع:**
   - في إعدادات خدمة Django
   - اذهب إلى قسم "Variables"
   - أضف متغير `DATABASE_URL` مع القيمة: `${{Postgres.DATABASE_URL}}`
   - هذا سيقوم بربط قاعدة البيانات تلقائياً

### 4. إعداد متغيرات البيئة

1. **المتغيرات الأساسية المطلوبة:**
   
   في إعدادات المشروع → Variables، أضف:

   ```env
   SECRET_KEY=your-secure-secret-key-here-minimum-50-characters
   DEBUG=False
   ALLOWED_HOSTS=*
   CSRF_TRUSTED_ORIGINS=https://*
   ```

2. **توليد SECRET_KEY آمن:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```

3. **متغيرات اختيارية:**
   ```env
   CUSTOM_DOMAIN=daluailiraq.com
   SITE_NAME=دلال
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-email-password
   ```

4. **متغيرات التواصل الاجتماعي (اختياري):**
   ```env
   SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your-google-client-id
   SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your-google-client-secret
   SOCIAL_AUTH_FACEBOOK_KEY=your-facebook-app-id
   SOCIAL_AUTH_FACEBOOK_SECRET=your-facebook-app-secret
   ```

### 5. مراقبة النشر

1. **مراقبة عملية البناء:**
   - Railway سيقوم ببناء المشروع تلقائياً
   - يمكنك مراقبة السجلات في تبويب "Build"
   - يستغرق البناء عادة 2-5 دقائق

2. **التحقق من صحة التطبيق:**
   - بعد اكتمال البناء، سيبدأ التطبيق تلقائياً
   - يمكنك مراقبة السجلات في تبويب "Logs"
   - تأكد من عدم وجود أخطاء

3. **فحص التطبيق:**
   - Railway سيوفر رابط عام مثل: `https://your-app-name.up.railway.app`
   - افتح الرابط في المتصفح للتحقق من عمل التطبيق

### 6. إعداد النطاق المخصص (اختياري)

1. **إضافة نطاق مخصص:**
   - في إعدادات المشروع → Settings → Domains
   - اضغط على "Add Domain"
   - أدخل نطاقك: `daluailiraq.com`

2. **تحديث إعدادات DNS:**
   - أضف سجل CNAME يشير إلى: `your-app-name.up.railway.app`
   - أو استخدم Railway's CNAME: `cname.railway.app`

3. **تحديث متغيرات البيئة:**
   ```env
   CUSTOM_DOMAIN=daluailiraq.com
   ALLOWED_HOSTS=daluailiraq.com,www.daluailiraq.com
   CSRF_TRUSTED_ORIGINS=https://daluailiraq.com,https://www.daluailiraq.com
   ```

## 🔧 ملفات التكوين المهمة

### railway.toml
```toml
[build]
builder = "DOCKERFILE"

[deploy]
healthcheckPath = "/health/"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[variables]
DEBUG = "False"
PORT = "8000"
PYTHONUNBUFFERED = "1"
PYTHONPATH = "/app"
DJANGO_SETTINGS_MODULE = "dalal_project.settings"
ALLOW_SQLITE_FALLBACK = "False"
GUNICORN_WORKERS = "2"
GUNICORN_THREADS = "4"
GUNICORN_TIMEOUT = "300"
```

### Dockerfile
- يستخدم Docker multi-stage build لتحسين الأداء
- يثبت جميع المتطلبات والمكتبات
- ينسخ سكريبتات البدء المطلوبة
- يضبط المنفذ 8000

### entrypoint.sh
- يتحقق من متغيرات البيئة المطلوبة
- يشغل الترحيلات (migrations)
- يجمع الملفات الثابتة
- يبدأ الخادم باستخدام Gunicorn

## 📊 مراقبة الأداء

### 1. Railway Dashboard
- **Build Logs**: مراقبة عملية البناء
- **Runtime Logs**: مراقبة سجلات التشغيل
- **Metrics**: مراقبة استخدام الموارد
- **Deploys**: تاريخ عمليات النشر

### 2. إعدادات الصحة
- يتم فحص صحة التطبيق على `/health/`
- إعادة التشغيل التلقائي عند الفشل
- حد أقصى 10 محاولات إعادة التشغيل

## 🛠️ استكشاف الأخطاء وإصلاحها

### مشكلة: DATABASE_URL غير موجود
**الحل:**
- تأكد من إضافة خدمة PostgreSQL
- تحقق من متغير `DATABASE_URL` في إعدادات Railway
- استخدم القيمة: `${{Postgres.DATABASE_URL}}`

### مشكلة: SECRET_KEY مفقود
**الحل:**
- أضف `SECRET_KEY` في متغيرات البيئة
- استخدم مفتاح آمن طويل (50+ حرف)
- لا تستخدم القيم الافتراضية

### مشكلة: فشل الترحيلات
**الحل:**
- تحقق من سجلات البناء
- تأكد من أن قاعدة البيانات متصلة
- جرب إعادة النشر بالقوة: أضف تعليق جديد في ملف تكوين

### مشكلة: الملفات الثابتة لا تعمل
**الحل:**
- تأكد من تشغيل `collectstatic` في entrypoint.sh
- تحقق من إعدادات WhiteNoise في settings.py
- أعد النشر إذا لزم الأمر

### مشكلة: أخطاء CSRF
**الحل:**
- تحقق من `CSRF_TRUSTED_ORIGINS` في متغيرات البيئة
- تأكد من إضافة نطاق Railway المخصص
- تحقق من إعدادات الكوكيز الآمنة

## 🔄 التحديثات والصيانة

### نشر تحديثات جديدة
```bash
# إجراء التغييرات المحلية
git add .
git commit -m "وصف التحديث"
git push origin main

# Railway سيقوم بالنشر تلقائياً
```

### إعادة النشر بالقوة
- أضف تعليق جديد في ملف تكوين (مثل `railway.toml`)
- ادفع التغييرات إلى GitHub
- Railway سيقوم ببناء جديد

### النسخ الاحتياطي لقاعدة البيانات
- Railway يقوم بعمل نسخ احتياطية تلقائية
- يمكنك تصدير قاعدة البيانات يدوياً من لوحة التحكم
- استخدم الأمر: `pg_dump` للنسخ الاحتياطي الخارجي

## 💰 التكاليف والفوترة

### Railway Pricing
- **Free Tier**: $5 شهرياً (بما في ذلك 512MB RAM)
- **PostgreSQL**: يبدأ من $5 شهرياً
- **Build Minutes**: 500 دقيقة مجانية شهرياً

### تقليل التكاليف
- استخدم النشر التلقائي فقط عند الحاجة
- أوقف الخدمات غير المستخدمة
- راقب استخدام الموارد بانتظام

## 🔒 الأمان

### أفضل الممارسات
- استخدم SECRET_KEY قوي وفريد
- لا تُثبت DEBUG=True في الإنتاج
- استخدم HTTPS دائماً
- حدث المكتبات بانتظام
- راقب السجلات للأنشطة المشبوهة

### حماية قاعدة البيانات
- المشروع مصمم لحماية قاعدة البيانات Railway PostgreSQL
- لا يستخدم SQLite في الإنتاج
- الترحيلات فقط (لا حذف أو إعادة تعيين)
- تحقق من متغير `ALLOW_SQLITE_FALLBACK=False`

## 📞 الدعم والمساعدة

### مصادر المساعدة
- Railway Documentation: https://docs.railway.app
- Django Documentation: https://docs.djangoproject.com
- GitHub Issues: افتح issue في مستودع المشروع

### المشاكل الشائعة
- راجع قسم استكشاف الأخطاء أعلاه
- تحقق من سجلات Railway
- تأكد من إعدادات متغيرات البيئة

## ✅ قائمة التحقق قبل النشر

- [ ] المشروع على GitHub
- [ ] ملفات التكوين موجودة (railway.toml, Dockerfile, Procfile)
- [ ] requirements.txt محدث
- [ ] SECRET_KEY آمن محدد
- [ ] DEBUG=False
- [ ] خدمة PostgreSQL مضافة
- [ ] DATABASE_URL مرتبط
- [ ] ALLOWED_HOSTS محدد
- [ ] CSRF_TRUSTED_ORIGINS محدد
- [ ] النطاق المخصص (اختياري)
- [ ] اختبار محلي ناجح
- [ ] مراجعة سجلات البناء

## 🎉 الخلاصة

بعد إكمال هذه الخطوات، سيكون تطبيق دلال يعمل على Railway بالكامل مع:
- قاعدة بيانات PostgreSQL آمنة
- بناء Docker محسن
- مراقبة صحة التطبيق
- إعادة تشغيل تلقائي عند الفشل
- ملفات ثابتة محسنة
- إعدادات أمان إنتاجية

للمساعدة الإضافية، راجع:
- `DEPLOYMENT_GUIDE.md` - دليل النشر العام
- `RAILWAY_DOMAIN_SETUP.md` - إعداد النطاق المخصص
- `DATABASE_PROTECTION_GUIDE.md` - حماية قاعدة البيانات