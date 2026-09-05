# دلال - إعدادات النظام الكاملة
## Dalal Project Settings Guide

هذا الدليل يشرح جميع إعدادات Django للمنصة وكيفية ضبطها للتطوير والإنتاج.

---

## 📋 جدول المحتويات

1. [المتغيرات البيئية الأساسية](#core-environment-variables)
2. [إعدادات الأمان](#security-settings)
3. [إعدادات قاعدة البيانات](#database-settings)
4. [إعدادات التخزين المؤقت](#cache-settings)
5. [إعدادات الملفات والوسائط](#media-file-settings)
6. [إعدادات البريد الإلكتروني](#email-settings)
7. [إعدادات الواجهة البرمجية](#api-settings)
8. [إعدادات الأداء](#performance-settings)
9. [إعدادات السجلات](#logging-settings)
10. [إعدادات الخصائص المتقدمة](#feature-flags)

---

## 🔑 المتغيرات البيئية الأساسية

### الإعدادات الأساسية
```bash
# وضع التطوير/الإنتاج
DEBUG=True|False

# مفتاح الأمان (مطلوب للإنتاج)
SECRET_KEY=your-secret-key-here

# النطاق المخصص
CUSTOM_DOMAIN=daluailiraq.com

# نطاق Railway العام
RAILWAY_PUBLIC_DOMAIN=muqq.up.railway.app
```

### قائمة المضيفين المسموح بهم
```bash
# المضيفون الإضافيين المسموح بهم (مفصولة بفواصل)
ALLOWED_HOSTS=localhost,127.0.0.1,example.com

# أصول CSRF الموثوقة (مفصولة بفواصل)
CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
```

---

## 🔒 إعدادات الأمان

### إعدادات ملفات تعريف الارتباط
```bash
# إعادة توجيه SSL للإنتاج
SECURE_SSL_REDIRECT=True

# أمان ملفات تعريف الارتباط
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
```

### إعدادات HSTS
```python
# يتم تعيين هذه تلقائياً بناءً على وضع DEBUG
SECURE_HSTS_SECONDS = 31536000  # سنة واحدة
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### إعدادات إضافية
```python
# رؤوس الأمان الإضافية
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
```

---

## 🗄️ إعدادات قاعدة البيانات

### إعدادات PostgreSQL (الإنتاج)
```bash
# URL قاعدة البيانات
DATABASE_URL=postgres://user:password@host:port/database

# أو المتغيرات المنفصلة
DB_NAME=dalal_production
DB_USER=dalal_user
DB_PASSWORD=secure_password
DB_HOST=postgres.railway.internal
DB_PORT=5432
```

### إعدادات إضافية
```bash
# حجم تجمع الاتصالات
DATABASE_CONNECTION_POOL_SIZE=10

# الحد الأقصى للاتصالات
DATABASE_MAX_CONNECTIONS=20

# مهلة الاستعلام
DATABASE_QUERY_TIMEOUT=30
```

---

## 💾 إعدادات التخزين المؤقت

### إعدادات Redis (الإنتاج)
```bash
# URL Redis
REDIS_URL=redis://redis.railway.internal:6379/0
```

### إعدادات المهلات
```bash
# المهلة الافتراضية (ثواني)
CACHE_TIMEOUT_DEFAULT=300

# مهلة البيانات الثابتة (ثواني)
CACHE_TIMEOUT_STATIC=3600

# مهلة نتائج الاستعلام (ثواني)
CACHE_TIMEOUT_QUERY=180
```

### التخزين المؤقت للإنتاج
عندما يكون `REDIS_URL` معيناً، سيتم استخدام Redis كخلفية التخزين المؤقت. في التطوير، يستخدم LocMemCache.

---

## 📁 إعدادات الملفات والوسائط

### قيود الملفات
```python
# حجم الذاكرة للرفع
DATA_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024  # 15MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024  # 15MB

# الحقول القصوى
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
```

### أنواع الملفات المسموحة
```python
# صور
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

# فيديو
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.webm', '.mov']
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB
```

### إعدادات الصور المصغرة
```python
THUMBNAIL_QUALITY = 85
THUMBNAIL_SIZE = (800, 600)
THUMBNAIL_FORMAT = 'JPEG'
```

---

## 📧 إعدادات البريد الإلكتروني

### إعدادات SMTP
```bash
# خلفية البريد الإلكتروني
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# إعدادات الخادم
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True

# بيانات المصادقة
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# عناوين البريد الإلكتروني
DEFAULT_FROM_EMAIL=noreply@daluailiraq.com
SERVER_EMAIL=admin@daluailiraq.com
```

### للتطوير
```bash
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

---

## 🔌 إعدادات الواجهة البرمجية

### قيود الواجهة البرمجية
```bash
# تفعيل قيود المعدل
RATELIMIT_ENABLE=True

# معدل الواجهة البرمجية
API_THROTTLE_RATE=1000/hour
API_THROTTLE_ANON=100/hour
```

### سجلات الواجهة البرمجية
```bash
# تفعيل سجلات طلبات الواجهة البرمجية
API_REQUEST_LOGGING=True
```

---

## ⚡ إعدادات الأداء

### إعدادات الاتصال
```python
# مهلة اتصال قاعدة البيانات
CONN_MAX_AGE = 600  # 10 دقائق

# التحقق من صحة الاتصال
conn_health_checks = True
```

### الوسائط الوسيطة للتخزين المؤقت
```python
# للإنتاج فقط
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = 'dalal'
CACHE_MIDDLEWARE_ANONYMOUS_ONLY = False
```

### ETags
```python
USE_ETAGS = True
```

---

## 📝 إعدادات السجلات

### ملفات السجلات
```python
# السجل الرئيسي
LOG_DIR / 'dalal.log'
maxBytes: 10MB
backupCount: 10

# سجل الأمان
LOG_DIR / 'security.log'
maxBytes: 5MB
backupCount: 5

# سجل الواجهة البرمجية
LOG_DIR / 'api.log'
maxBytes: 10MB
backupCount: 5
```

### مستويات السجلات
```python
# Django: WARNING
# Django Security: WARNING
# Properties: INFO
# API Views: INFO
```

---

## 🚩 إعدادات الخصائص المتقدمة

### الخصائص التفاعلية
```bash
# عروض العقارات
FEATURE_ENABLED_PROPERTY_OFFERS=True

# المفاوضات
FEATURE_ENABLED_NEGOTIATIONS=True

# الحجوزات
FEATURE_ENABLED_RESERVATIONS=True

# الخريطة التفاعلية
FEATURE_ENABLED_INTERACTIVE_MAP=True

# البحث بالذكاء الاصطناعي
FEATURE_ENABLED_AI_SEARCH=False

# الجولات الافتراضية
FEATURE_ENABLED_VIRTUAL_TOURS=True
```

### إعدادات الوسائط
```bash
# أقصى عدد عقارات للوسيط
MAX_PROPERTIES_PER_BROKER=100

# أقصى عدد صور للعقار
MAX_IMAGES_PER_PROPERTY=20

# أقصى عدد فيديوهات للعقار
MAX_VIDEOS_PER_PROPERTY=5
```

### إعدادات الخريطة
```python
DEFAULT_MAP_CENTER_LAT = 33.3152  # بغداد
DEFAULT_MAP_CENTER_LNG = 44.3661
DEFAULT_MAP_ZOOM = 12
```

---

## 🔔 إعدادات الإشعارات

### إشعارات الويب (VAPID)
```bash
# مفتاح VAPID العام
VAPID_PUBLIC_KEY=your-vapid-public-key

# مفتاح VAPID الخاص
VAPID_PRIVATE_KEY=your-vapid-private-key

# البريد الإلكتروني للمطالبة
VAPID_CLAIM_EMAIL=admin@daluailiraq.com
```

### إعدادات الإشعارات
```python
NOTIFICATION_EXPIRY_DAYS = 30
NOTIFICATION_MAX_PER_USER = 1000
```

---

## 📊 إعدادات التحليلات

### Google Analytics
```bash
ANALYTICS_ENABLED=True
GOOGLE_ANALYTICS_ID=GA_MEASUREMENT_ID
```

### Facebook Pixel
```bash
FACEBOOK_PIXEL_ID=your-pixel-id
```

---

## 🛠️ إعدادات التطوير

### شريط تصحيح الأخطاء
```bash
DEBUG_TOOLBAR_ENABLED=True
```

### Django Extensions
يتم تفعيل django_extensions تلقائياً في وضع التطوير إذا كان متاحاً.

---

## 🚨 إعدادات الإبلاغ عن الأخطاء

### Sentry
```bash
SENTRY_DSN=your-sentry-dsn
```

عند تعيين DSN، سيتم تفعيل الإبلاغ عن الأخطاء تلقائياً في الإنتاج.

---

## 📦 إعدادات النسخ الاحتياطي

```bash
# تفعيل النسخ الاحتياطي
BACKUP_ENABLED=True

# جدولة النسخ الاحتياطي (cron)
BACKUP_SCHEDULE=0 2 * * *  # يومياً الساعة 2 صباحاً

# مدة الاحتفاظ بالنسخ الاحتياطية
BACKUP_RETENTION_DAYS=30
```

---

## 🎯 إعدادات البحث والتصفية

```python
SEARCH_MIN_CHARS = 2
SEARCH_MAX_RESULTS = 100
FILTER_MAX_OPTIONS = 50
```

---

## 🌐 إعدادات SEO

```bash
SEO_DEFAULT_TITLE=دلال - منصة العقارات العراقية
SEO_DEFAULT_DESCRIPTION=أفضل منصة للبحث عن العقارات في العراق
SEO_DEFAULT_KEYWORDS=عقارات, عقارات العراق, بيع, شراء, تأجير, دلال
SOCIAL_SHARE_IMAGE=/static/images/og-default.jpg
```

---

## 🔄 إعدادات WebSocket

```bash
USE_WEBSOCKETS=True
```

عند التفعيل، سيتم إضافة إعدادات Channels تلقائياً.

---

## 📝 إعدادات الصيانة

```bash
MAINTENANCE_MODE=False
MAINTENANCE_MESSAGE=الموقع قيد الصيانة - سنعود قريباً
```

---

## 🚀 التحضير للإنتاج

### خطوات ضرورية:

1. **تعيين متغيرات البيئة الأساسية**
   ```bash
   DEBUG=False
   SECRET_KEY=your-secure-random-key
   SECURE_SSL_REDIRECT=True
   ```

2. **إعداد قاعدة البيانات**
   ```bash
   DATABASE_URL=postgres://user:password@host:port/database
   ```

3. **إعداد Redis**
   ```bash
   REDIS_URL=redis://redis.railway.internal:6379/0
   ```

4. **إعداد البريد الإلكتروني**
   ```bash
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   ```

5. **إعداد إشعارات الويب**
   ```bash
   VAPID_PUBLIC_KEY=your-vapid-public-key
   VAPID_PRIVATE_KEY=your-vapid-private-key
   ```

6. **إعداد الإبلاغ عن الأخطاء (اختياري)**
   ```bash
   SENTRY_DSN=your-sentry-dsn
   ```

7. **إعداد التحليلات (اختياري)**
   ```bash
   ANALYTICS_ENABLED=True
   GOOGLE_ANALYTICS_ID=GA_MEASUREMENT_ID
   ```

---

## 🔍 التحقق من الإعدادات

### فحص Django الأساسي
```bash
python manage.py check
```

### فحص إعدادات الإنتاج
```bash
python manage.py check --deploy
```

### عرض الإعدادات النشطة
```bash
python manage.py diffsettings
```

---

## 📚 المزيد من المعلومات

- [Django Settings Documentation](https://docs.djangoproject.com/en/stable/ref/settings/)
- [Django Security](https://docs.djangoproject.com/en/stable/topics/security/)
- [Railway Environment Variables](https://docs.railway.app/reference/variables)

---

**ملاحظة مهمة**: تأكد دائماً من عدم تعريف مفاتيح الأمان الحساسة في الكود المصدري. استخدم دائماً متغيرات البيئة في الإنتاج.