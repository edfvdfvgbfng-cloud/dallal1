# 🛡️ دليل حماية قاعدة البيانات على Railway

## 📋 ملخص الحماية

هذا المشروع مصمم بحيث **لا يمكن حذف أو تصفير قاعدة البيانات PostgreSQL على Railway** عند أي deploy جديد من GitHub.

## ✅ الضمانات المطبقة

### 1. **ضمانات على مستوى Settings (settings.py)**
- **رفض صريح لـ SQLite في Production:**
  ```python
  if not DEBUG and DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
      raise ValueError("CRITICAL: SQLite is not allowed in production...")
  ```
- **رفض إذا لم يكن DATABASE_URL موجوداً:**
  ```python
  raise ValueError("CRITICAL: DATABASE_URL must be set in production...")
  ```
- **Validation لمنع القيم الباطلة:**
  ```python
  invalid_patterns = ['@host:', 'user:password@']
  if any(pattern in database_url for pattern in invalid_patterns):
      database_url = None
  ```

### 2. **ضمانات على مستوى Railway (railway.toml)**
```toml
ALLOW_SQLITE_FALLBACK = "False"
```
- منع أي fallback إلى SQLite في production

### 3. **ضمانات على مستوى Deploy (run_server.py)**
```python
# CRITICAL: Using --noinput to prevent any destructive operations
run([sys.executable, 'manage.py', 'migrate', '--noinput'], allow_fail=True)
```
- استخدام `--noinput` فقط
- **لا يتم استخدام:**
  - ❌ `flush`
  - ❌ `reset`
  - ❌ `makemigrations`
  - ❌ `DROP TABLE`
  - ❌ `DROP DATABASE`

### 4. **ضمانات على مستوى Migrations**
- **تم تعديل Migration 0055_create_superuser.py:**
  - Reverse migration لا يحذف المستخدم (كان يحذف `muqtada123`)
  - الآن: `pass` (لا يفعل شيئاً لحماية البيانات)

- **تم تعديل Migration 0068_auctionparticipant_approval_status_and_more.py:**
  - كان يستخدم SQLite-specific query (`sqlite_master`)
  - الآن يستخدم database-agnostic method (`connection.introspection.table_names()`)
  - يعمل بشكل صحيح على PostgreSQL

### 5. **ضمانات على مستوى Git (.gitignore)**
```
db.sqlite3
db.sqlite3-journal
*.sqlite3
```
- ملفات SQLite المحلية محمية من Git
- لا يمكن حذف قاعدة البيانات عن طريق Git

## 🚀 عملية Deploy الآمنة

عند كل deploy جديد من GitHub إلى Railway:

1. ✅ **تحقق من DATABASE_URL**
   - Railway يوفر `DATABASE_URL` تلقائياً
   - Django يتصل بقاعدة PostgreSQL الحالية

2. ✅ **تشغيل migrations فقط**
   ```bash
   python manage.py migrate --noinput
   ```
   - يطبق migrations الجديدة فقط
   - لا يحذف أي بيانات
   - لا يعدل migrations القديمة

3. ✅ **جمع static files**
   ```bash
   python manage.py collectstatic --noinput
   ```

4. ✅ **تشغيل Gunicorn**
   - يتصل بقاعدة PostgreSQL الحالية
   - لا يقوم بأي عملية على قاعدة البيانات

## ❌ العمليات المحظورة

هذه العمليات **لا يتم تنفيذها أبداً** في production:

- ❌ `python manage.py flush` - يحذف جميع البيانات
- ❌ `python manage.py reset` - يعيد تعيين قاعدة البيانات
- ❌ `python manage.py makemigrations` - ينشئ migrations جديدة (dev only)
- ❌ `DROP TABLE` أو `DROP DATABASE` SQL commands
- ❌ حذف ملف `db.sqlite3` (محلي فقط)
- ❌ `python manage.py migrate --fake` بشكل غير آمن
- ❌ أي seed يحذف البيانات القديمة

## 🔒 اختبار الحماية

يمكنك اختبار الحماية بتشغيل:

```bash
# في production (على Railway)
# محاولة استخدام SQLite ستفشل
DEBUG=False DATABASE_URL=sqlite:///db.sqlite3 python manage.py runserver
# Output: ValueError: CRITICAL: SQLite is not allowed in production...

# محاطة بدون DATABASE_URL ستفشل
DEBUG=False python manage.py runserver
# Output: ValueError: CRITICAL: DATABASE_URL must be set in production...
```

## 📊 ما يحدث عند Deploy جديد

### ✅ **السيناريو الطبيعي:**
1. GitHub يرسل الكود الجديد إلى Railway
2. Railway يبني Docker image
3. Railway يبدأ الحاوية مع:
   - `DATABASE_URL` الحالي ( Railway PostgreSQL)
   - `DEBUG=False`
4. `run_server.py` يعمل:
   - `migrate --noinput` - يطبق migrations جديدة فقط
   - `collectstatic --noinput` - يجمع static files
   - `gunicorn` - يبدأ السيرفر
5. **النتيجة:** قاعدة البيانات الحالية محفوظة ✅

### ❌ **السيناريو الخطير (محظور):**
1. محاولة استخدام SQLite في production
2. **النتيجة:** التطبيق يرفض البدء ❌
3. **التأثير:** قاعدة البيانات محمية ✅

## 🔄 ما الذي يتم حفظه بين Deploys

كل هذه البيانات **تبقى محفوظة** على Railway PostgreSQL:

- ✅ المستخدمين (Users)
- ✅ العقارات (Properties)
- ✅ الإعلانات (Advertisements)
- ✅ الحجوزات (Bookings)
- ✅ المزادات (Auctions)
- ✅ المحادثات (Messages/Conversations)
- ✅ التقييمات (Ratings)
- ✅ الاشتراكات (Subscriptions)
- ✅ أي بيانات أخرى في قاعدة البيانات

## 📝 القاعدة الأساسية

**الكود يمكن تحديثه أو استبداله، لكن البيانات PostgreSQL الموجودة على Railway تبقى محفوظة كما هي.**

- GitHub = الكود فقط
- Railway PostgreSQL = البيانات فقط
- Deploy = تحديث الكود + تطبيق migrations آمنة
- **لا حذف، لا reset، لا flush تحت أي ظرف**

## 🆘 ماذا تفعل إذا حدثت مشكلة

إذا فشل migration في production:

1. **لا تقم بـ:**
   - ❌ `python manage.py flush`
   - ❌ حذف قاعدة البيانات من Railway
   - ❌ إنشاء قاعدة بيانات جديدة

2. **قم بـ:**
   - ✅ راجع الـ migration التي فشلت
   - ✅ تأكد أنها لا تحتوي على عمليات حذف خطيرة
   - ✅ أصلح المشكلة في الـ migration
   - ✅ أرسل fix جديد إلى GitHub
   - ✅ Railway سيقوم بـ deploy جديد تلقائياً

## 📞 الدعم

إذا واجهت أي مشاكل مع قاعدة البيانات على Railway:

1. راجع `DATABASE_URL` في Railway dashboard
2. تأكد أن `DEBUG=False` في production
3. راجع logs في Railway لمعرفة الخطأ
4. تأكد أن الـ migrations لا تحتوي على عمليات حذف

---

**آخر تحديث:** 2026-09-03  
**الإصدار:** 1.0  
**الحالة:** ✅ محمي بالكامل