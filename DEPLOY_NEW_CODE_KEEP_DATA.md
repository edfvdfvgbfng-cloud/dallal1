# دليل النشر - رفع كود جديد مع الحفاظ على قاعدة البيانات الموجودة

## السيناريو
- لديك **ملف مشروع جديد محدث** (بدون قاعدة بيانات)
- لديك **مشروع قديم على GitHub/Railway** (مع قاعدة بيانات)
- تريد **رفع الملف الجديد** إلى GitHub وRailway
- تريد **البيانات القديمة أن تبقى محفوظة**

---

## 🔑 النقطة الأساسية

**البيانات لا تخزن في الكود!**

- **الكود** = الملفات (views.py, models.py, templates, etc.)
- **البيانات** = ما في قاعدة البيانات (users, properties, messages, etc.)

على Railway:
- **الكود** في `web service`
- **البيانات** في `PostgreSQL service` (منفصل تماماً)

عندما ترفع كود جديد:
- ✅ الكود يتحدث
- ✅ البيانات تبقى في PostgreSQL service (لا تتأثر)

---

## 📋 خطوات النشر الآمن

### الخطوة 1: تحقق من الحالة الحالية

#### على جهازك المحلي:
```bash
# تأكد من أنك في المشروع الجديد المحدث
cd "C:\Users\moktata\Desktop\moq-main (3)\moq-main"

# تحقق من أن ملفات db.sqlite3 ليست موجودة
# إذا كانت موجودة، احذفها
del db.sqlite3
del muq.sqlite3
```

#### على Railway Dashboard:
1. افتح https://railway.app
2. سجل الدخول
3. افتح مشروع `dallal1`
4. تأكد من وجود **PostgreSQL service**
5. تأكد من وجود **web service**
6. اضغط على PostgreSQL service
7. اضغط على "Variables"
8. انسخ `DATABASE_URL` (ستحتاجه لاحقاً)

### الخطوة 2: جهز المشروع الجديد للنشر

#### على جهازك المحلي:
```bash
# 1. تأكد من أن .gitignore يحتوي على ملفات SQLite
# افتح .gitignore وتأكد من وجود:
# db.sqlite3
# *.sqlite3
# muq.sqlite3

# 2. تأكد من أن railway.toml موجود وصحيح
# يجب أن يحتوي على:
# ALLOW_SQLITE_FALLBACK = "False"

# 3. تأكد من أن Dockerfile موجود وصحيح
# يجب أن يحتوي على:
# ENV ALLOW_SQLITE_FALLBACK=False

# 4. تشغيل سكريبت التحقق
python scripts/verify_railway_setup.py
```

إذا فشل السكريبت، أصلح المشاكل قبل المتابعة.

### الخطوة 3: اربط المشروع الجديد بالـ GitHub القديم

#### خيار أ: إذا كنت تريد استبدال الكود القديم بالكامل

```bash
# 1. انتقل إلى المشروع الجديد
cd "C:\Users\moktata\Desktop\moq-main (3)\moq-main"

# 2. إزالة git القديم (إذا كان موجوداً)
rm -rf .git

# 3. تهيئة git جديد
git init

# 4. أضف ملفات الكود الجديد
git add .

# 5. أول commit
git commit -m "Initial commit - Updated code with data protection"

# 6. أضف remote للـ GitHub القديم
git remote add origin https://github.com/edfvdfvgbfng-cloud/dallal1.git

# 7. اضغط الكود (سيستبدل الكود القديم)
git push -f origin main
# أو إذا كان الفرع مختلف:
git push -f origin master
```

**⚠️ تحذير:** `git push -f` سيحذف الكود القديم من GitHub ويستبدله بالكود الجديد. البيانات في Railway لن تتأثر.

#### خيار ب: إذا كنت تريد دمج الكود الجديد مع القديم

```bash
# 1. انتقل إلى المشروع الجديد
cd "C:\Users\moktata\Desktop\moq-main (3)\moq-main"

# 2. استنساخ الكود القديم
git clone https://github.com/edfvdfvgbfng-cloud/dallal1.git dallal1-old

# 3. انسخ ملفات الكود الجديد إلى المجلد القديم
# (يدوياً أو باستخدام أوامر copy)

# 4. انتقل إلى المجلد القديم
cd dallal1-old

# 5. اضغط التغييرات
git add .
git commit -m "Merge updated code"
git push origin main
```

### الخطوة 4: تفعيل Railway على GitHub

#### على Railway Dashboard:
1. افتح مشروع `dallal1`
2. اضغط على "New Project"
3. اختر "Deploy from GitHub repo"
4. اختر المستودع `edfvdfvgbfng-cloud/dallal1`
5. Railway سيقوم تلقائياً بإعادة النشر

أو إذا كان المشروع موجوداً بالفعل:
1. افتح مشروع `dallal1`
2. اضغط على "Settings"
3. اضغط على "GitHub"
4. تأكد من أن المستودع مرتبط
5. Railway سيقوم تلقائياً بإعادة النشر عند كل push

### الخطوة 5: تأكد من أن Railway يستخدم PostgreSQL الصحيح

#### على Railway Dashboard:
1. افتح مشروع `dallal1`
2. اضغط على **web service**
3. اضغط على "Variables"
4. تأكد من وجود:
   ```
   DATABASE_URL=postgres://...
   ```
5. إذا لم يكن موجوداً، أضفه من **PostgreSQL service**:
   - اضغط على PostgreSQL service
   - اضغط على "Variables"
   - انسخ `DATABASE_URL`
   - العودة إلى web service
   - أضف `DATABASE_URL` مع القيمة المنسوخة

### الخطوة 6: إعادة نشر التطبيق

#### على Railway Dashboard:
1. افتح مشروع `dallal1`
2. اضغط على **web service**
3. اضغط على "Redeploy"
4. انتظر حتى يكتمل النشر

أو من GitHub:
```bash
# إذا قمت بتغيير الكود، اضغط التغييرات
git add .
git commit -m "Update code"
git push
# Railway سيقوم تلقائياً بإعادة النشر
```

### الخطوة 7: تحقق من أن البيانات محفوظة

#### بعد اكتمال النشر:
```bash
# على Railway Dashboard، افتح Terminal
# أو استخدم Railway CLI

# عد البيانات
python manage.py shell -c "from django.contrib.auth.models import User; print('Users:', User.objects.count())"
python manage.py shell -c "from properties.models import Property; print('Properties:', Property.objects.count())"
```

أو من المتصفح:
1. افتح موقعك على Railway
2. سجل الدخول
3. تحقق من أن بياناتك موجودة

---

## ✅ قائمة التحقق

قبل النشر:
- [ ] المشروع الجديد لا يحتوي على ملفات SQLite
- [ ] .gitignore يحتوي على db.sqlite3, *.sqlite3
- [ ] railway.toml يحتوي على ALLOW_SQLITE_FALLBACK = "False"
- [ ] Dockerfile يحتوي على ENV ALLOW_SQLITE_FALLBACK=False
- [ ] run_server.py يستخدم migrate --noinput
- [ ] سكريبت verify_railway_setup.py ينجح

على Railway:
- [ ] PostgreSQL service موجود
- [ ] DATABASE_URL في web service يشير إلى PostgreSQL
- [ ] لا يتم حذف PostgreSQL service

بعد النشر:
- [ ] التطبيق يعمل بشكل صحيح
- [ ] البيانات القديمة موجودة
- [ ] لا توجد أخطاء في logs

---

## 🚨 ما يجب تجنبه

❌ **لا تفعل هذا:**
- ❌ حذف PostgreSQL service على Railway
- ❌ تغيير DATABASE_URL على Railway
- ❌ استخدام `flush` أو `reset` في الإنتاج
- ❌ إضافة migrations تحذف البيانات
- ❌ حذف ملفات migrations من git

✅ **افعل هذا:**
- ✅ استخدام `migrate --noinput` فقط
- ✅ الحفاظ على PostgreSQL service
- ✅ التحقق من DATABASE_URL قبل النشر
- ✅ عمل backup قبل التغييرات الكبيرة

---

## 🔧 استكشاف الأخطاء

### المشكلة: البيانات مفقودة بعد النشر

#### الحل 1: تحقق من PostgreSQL service
1. افتح Railway Dashboard
2. تأكد من أن PostgreSQL service موجود
3. إذا تم حذفه بالخطأ، لا يمكن استعادة البيانات

#### الحل 2: تحقق من DATABASE_URL
1. افتح web service على Railway
2. اضغط على "Variables"
3. تأكد من أن DATABASE_URL يشير إلى PostgreSQL
4. إذا كان يشير إلى SQLite، صححه

#### الحل 3: استعادة من backup
1. افتح PostgreSQL service على Railway
2. اضغط على "Backups"
3. اختر النسخة قبل النشر
4. اضغط "Restore"

### المشكلة: لا يمكن النشر

#### الحل:
1. تحقق من أن GitHub مرتبط بـ Railway
2. تحقق من أن railway.toml موجود
3. تحقق من أن Dockerfile موجود
4. راجع logs على Railway

---

## 📞 المساعدة

إذا واجهت مشاكل:
1. راجع `RAILWAY_DATA_PROTECTION.md`
2. راجع `QUICK_START_RAILWAY.md`
3. شغّل `python scripts/verify_railway_setup.py`
4. تحقق من Railway logs

---

## 🎯 الخلاصة

**البيانات محفوظة تلقائياً إذا:**
1. PostgreSQL service موجود على Railway
2. DATABASE_URL يشير إلى PostgreSQL
3. لا تستخدم `flush` أو `reset`
4. ALLOW_SQLITE_FALLBACK = False

**عند رفع كود جديد:**
- ✅ الكود يتحدث
- ✅ البيانات تبقى في PostgreSQL service
- ✅ Railway يقوم تلقائياً بإعادة النشر
- ✅ لا حاجة لأي إجراءات خاصة

**مهم:** البيانات في PostgreSQL service منفصل تماماً عن الكود. رفع كود جديد لن يؤثر على البيانات إذا تم اتباع الإرشادات أعلاه.
