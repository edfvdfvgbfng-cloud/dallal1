# دليل التطوير - منصة دلال العقارية

## نظرة عامة على المشروع

منصة دلال هي منصة عقارات عراقية متكاملة مبنية على Django 5.0+ مع Python 3.11، توفر نظاماً شاملاً لإدارة وعرض العقارات مع ميزات متقدمة للدلالين والمستخدمين.

## البنية التقنية

### Backend
- **Framework**: Django 5.0+
- **Language**: Python 3.11+
- **Database**: SQLite (التطوير) / PostgreSQL (الإنتاج)
- **API**: Django REST Framework
- **Authentication**: Django Auth + Social Auth (Google, Facebook)
- **Cache**: Django Cache with Redis support
- **Static Files**: WhiteNoise

### Frontend
- **HTML5/CSS3/JavaScript**: Vanilla JS with modern ES6+
- **CSS Framework**: Custom design system with premium UI
- **Maps**: Leaflet.js with MarkerCluster
- **Icons**: SVG icons
- **PWA**: Progressive Web App support

## إعداد بيئة التطوير

### المتطلبات الأساسية
```bash
# Python 3.11+
python --version

# Virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

### تثبيت المكتبات
```bash
pip install -r requirements.txt
```

### إعداد قاعدة البيانات
```bash
python manage.py migrate
python manage.py createsuperuser
```

### تشغيل الخادم
```bash
python manage.py runserver
```

## هيكل المشروع

```
moq-main/
├── dalal_project/          # إعدادات Django الرئيسية
│   ├── settings.py         # إعدادات المشروع
│   ├── urls.py             # مسارات URL الرئيسية
│   └── wsgi.py             # WSGI configuration
├── properties/             # التطبيق الرئيسي
│   ├── models.py          # نماذج البيانات
│   ├── views.py           # الوظائف الرئيسية
│   ├── forms.py           # النماذج
│   ├── admin.py           # لوحة تحكم Django
│   ├── urls.py            # مسارات URL للتطبيق
│   ├── api_views.py       # واجهات API
│   ├── serializers.py     # تسلسل API
│   ├── mixins.py          # Mixins المشتركة
│   ├── database_optimizations.py  # تحسينات قاعدة البيانات
│   ├── tests.py           # الاختبارات
│   ├── constants.py       # الثوابت
│   ├── utils.py           # الوظائف المساعدة
│   ├── permissions.py     # الصلاحيات
│   ├── middleware.py      # البرمجيات الوسيطة
│   ├── signals.py         # الإشارات
│   ├── templates/         # قوالب HTML
│   └── static/            # الملفات الثابتة
├── static/                # الملفات الثابتة العامة
│   ├── css/              # ملفات CSS
│   ├── js/               # ملفات JavaScript
│   └── images/           # الصور
├── templates/             # القوالب العامة
├── media/                 # الملفات المرفوعة
├── logs/                  # سجلات النظام
└── manage.py             # أوامر Django
```

## الميزات الرئيسية

### نظام العقارات
- إدارة كاملة للعقارات (أراضي، بيوت، بنايات، شقق، محلات تجارية)
- فلترة متقدمة حسب النوع، الحالة، السعر، الموقع، والمزيد
- خرائط تفاعلية مع Leaflet.js
- نظام الصور والفيديو
- الجولات الافتراضية 360°

### نظام الدلالين
- لوحة تحكم شاملة للدلالين
- نظام اشتراكات متعدد المستويات
- إحصائيات متقدمة وتقارير
- نظام المراسلة
- إدارة العقارات والمزادات

### نظام المزادات
- إنشاء وإدارة المزادات
- نظام المزايدة التلقائي
- دخول المشترين المحمول بكود
- بث مباشر للمزادات

### نظام الفنادق والمنتجعات
- إدارة الفنادق والمنتجعات
- نظام الحجز
- عرض المرافق والخدمات
- التقييمات والمراجعات

### نظام الوظائف
- نشر فرص العمل
- التقديم على الوظائف
- إدارة الطلبات

## الأمان

### إعدادات الأمان المحسنة
- **XSS Protection**: `SECURE_BROWSER_XSS_FILTER = True`
- **Content Type Protection**: `SECURE_CONTENT_TYPE_NOSNIFF = True`
- **Clickjacking Protection**: `X_FRAME_OPTIONS = 'DENY'`
- **HSTS**: Enabled in production
- **Cookie Security**: HTTPOnly and Secure cookies in production
- **CSRF Protection**: Enabled by default

### صلاحيات المستخدمين
- نظام صلاحيات متعدد المستويات
- التحقق من الصلاحيات في كل عملية حساسة
- حماية البيانات الحساسة

## الأداء

### تحسينات قاعدة البيانات
- **Indexes**: فهارس محسنة للاستعلامات الشائعة
- **Query Optimization**: استخدام select_related و prefetch_related
- **Materialized Views**: طرق عرض مادية للبيانات المعقدة
- **Connection Pooling**: إدارة اتصالات قاعدة البيانات

### تحسينات Frontend
- **Lazy Loading**: تحميل الصور عند الحاجة
- **Debouncing**: للبحث والطلبات المتكررة
- **Caching**: caching للمحتوى الثابت والدينامي
- **Minification**: CSS و JavaScript مضغوط

## اختبار المشروع

### تشغيل الاختبارات
```bash
# تشغيل جميع الاختبارات
python manage.py test

# تشغيل اختبارات تطبيق معين
python manage.py test properties

# تشغيل اختبارات مع تفاصيل
python manage.py test properties --verbosity=2

# تشغيل اختبارات الأداء
python manage.py test properties.PerformanceTest
```

### أنواع الاختبارات
- **Unit Tests**: اختبارات الوحدات للنماذج والدوال
- **Integration Tests**: اختبارات التكامل للعمليات الكاملة
- **API Tests**: اختبارات واجهات API
- **Performance Tests**: اختبارات الأداء

## النشر

### على Railway
1. ربط المستودع مع GitHub
2. إضافة خدمة PostgreSQL
3. إعداد متغيرات البيئة:
   ```
   SECRET_KEY=your-secure-secret-key
   DEBUG=False
   ALLOWED_HOSTS=*
   CSRF_TRUSTED_ORIGINS=https://*
   DATABASE_URL=(تضاف تلقائياً)
   ```

### على Docker
```bash
# بناء الصورة
docker build -t dalal-app .

# تشغيل الحاوية
docker run -p 8000:8000 dalal-app
```

## الصيانة

### أوامر الإدارة
```bash
# تحسين قاعدة البيانات
python manage.py shell -c "from properties.database_optimizations import setup_database_optimizations; setup_database_optimizations()"

# تحديث طرق العرض المادية
python manage.py shell -c "from properties.database_optimizations import refresh_materialized_views; refresh_materialized_views()"

# تنظيف الملفات القديمة
python manage.py cleanup_expired_properties
python manage.py auto_freeze_expired
```

## استكشاف الأخطاء

### المشاكل الشائعة

#### خطأ في الاتصال بقاعدة البيانات
```bash
# إعادة إنشاء قاعدة البيانات
rm db.sqlite3
python manage.py migrate
```

#### مشاكل في الملفات الثابتة
```bash
# إعادة جمع الملفات الثابتة
python manage.py collectstatic --noinput --clear
```

#### أخطاء في الهجرات
```bash
# عرض حالة الهجرات
python manage.py showmigrations

# إعادة تطبيق الهجرات
python manage.py migrate --fake-initial
```

## الممارسات البرمجية

### كتابة الكود
- اتبع PEP 8 للكود Python
- استخدم docstrings للتوثيق
- اكتب اختبارات للكود الجديد
- استخدم git flow لإدارة الإصدارات

### إدارة الاعتماديات
- استخدم `requirements.txt` للاعتماديات الأساسية
- استخدم virtualenv لعزل البيئة
- حدث المكتبات بانتظام

### الأمان
- لا تودع ملفات `.env` في git
- استخدم متغيرات البيئة للبيانات الحساسة
- راجع الكود بحثاً عن ثغرات أمنية

## الموارد

### التوثيق الرسمي
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Python Documentation](https://docs.python.org/)

### الأدوات
- [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/)
- [Sentry](https://sentry.io/) - Error tracking
- [New Relic](https://newrelic.com/) - Performance monitoring

## الدعم والتواصل

للدعم والمساعدة:
- البريد الإلكتروني: support@daluailiraq.com
- التوثيق: راجع الملفات في مجلد `docs/`
- المشاكل: أنشأ issue على GitHub

## الترخيص

هذا المشروع مرخص تحت MIT License.