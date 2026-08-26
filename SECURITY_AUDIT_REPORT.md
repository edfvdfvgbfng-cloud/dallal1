# تقرير مراجعة الأمن الشاملة
## مشروع دلال - منصة العقارات العراقية
**التاريخ:** 2026-08-15
**المُنفذ:** مهندس أمن معلومات
**الحالة:** ✅ منجز

---

## ملخص تنفيذي

تم إجراء مراجعة أمنية شاملة لمشروع دلال، منصة العقارات العراقية. تشمل المراجعة تحليل إعدادات Django، نقاط النهاية API، رفع الملفات، حقن SQL، XSS، CSRF، تقييد المعدل، إدارة الأسرار، وأمان قاعدة البيانات.

### النتيجة العامة
**🟡 متوسط - يحتاج إلى تحسينات**

---

## 1. إعدادات Django (settings.py)

### ✅ الإيجابيات
- تم استخدام ALLOWED_HOSTS بشكل صحيح
- تم تفعيل CSRF protection
- تم تفعيل HSTS للإنتاج
- تم تفعيل X-Frame-Options: DENY
- تم تفعيل SECURE_BROWSER_XSS_FILTER
- تم تفعيل SECURE_CONTENT_TYPE_NOSNIFF
- تم استخدام environment variables للأسرار
- تم تفعيل كلمات مرور قوية (password validators)
- تم تفعيل rate limiting في REST Framework

### ⚠️ المشاكل

#### 1.1 DEBUG Mode
**الخطورة:** 🔴 عالية
```python
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
```
**المشكلة:** القيمة الافتراضية هي True في حالة عدم وجود متغير البيئة.
**التوصية:** يجب أن تكون القيمة الافتراضية False:
```python
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

#### 1.2 ALLOWED_HOSTS يحتوي على '*'
**الخطورة:** 🟡 متوسطة
```python
ALLOWED_HOSTS = ['*']
```
**المشكلة:** قبول جميع الأسماء يُعرض الموقع لهجمات Host Header Injection.
**التوصية:** إزالة '*' والاعتماد فقط على القوائم المحددة:
```python
ALLOWED_HOSTS = _parse_csv_env('ALLOWED_HOSTS')
```

#### 1.3 SECRET_KEY الافتراضي للتطوير
**الخطورة:** 🔴 عالية
```python
if DEBUG:
    SECRET_KEY = 'django-insecure-local-dev-only-change-me'
```
**المشكلة:** استخدام مفتاح سري ثابت ومعلن في الكود.
**التوصية:** يجب توفير SECRET_KEY عبر environment variable حتى في التطوير.

#### 1.4 CSRF Cookie ليس HTTPOnly
**الخطورة:** 🟡 متوسطة
```python
CSRF_COOKIE_HTTPONLY = False
```
**المشكلة:** CSRF cookie يمكن الوصول إليه عبر JavaScript.
**التوصية:** تفعيل HTTPOnly:
```python
CSRF_COOKIE_HTTPONLY = True
```

#### 1.5 CORS Allow All Origins في DEBUG
**الخطورة:** 🟡 متوسطة
```python
CORS_ALLOW_ALL_ORIGINS = DEBUG
```
**المشكلة:** في وضع التطوير، يتم قبول جميع الأصول.
**التوصية:** تحديد الأصول المسموح بها بوضوح حتى في التطوير.

---

## 2. نقاط النهاية API (API Endpoints)

### ✅ الإيجابيات
- معظم نقاط النهاية تستخدم @login_required
- نقاط الإدارة تستخدم @staff_required
- بعض العمليات الحساسة تستخدم @require_POST
- استخدام Django ORM يمنع SQL injection

### ⚠️ المشاكل

#### 2.1 نقطة النهاية AI Chat مفتوحة للجميع
**الخطورة:** 🟡 متوسطة
```python
@api_view(['POST'])
@permission_classes([AllowAny])
def ai_chat(request):
```
**المشكلة:** أي شخص يمكنه استخدام AI Gateway بدون تسجيل دخول.
**التوصية:** إضافة تقييد معدل وتسجيل محاولات الاستخدام غير المصرح به.

#### 2.2 نقطة النهاية Legacy Chatbot مفتوحة
**الخطورة:** 🟡 متوسطة
```python
@api_view(['POST'])
@permission_classes([AllowAny])
def ai_chatbot_legacy(request):
```
**المشكلة:** نفس المشكلة السابقة - نقطة التكافؤ مفتوحة.
**التوصية:** إضافة نفس الحماية.

#### 2.3 بعض النقاط الحساسة تفتقر إلى @require_POST
**الخطورة:** 🟡 متوسطة
**المشكلة:** بعض العمليات الحساسة يمكن استدعاؤها عبر GET.
**التوصية:** إضافة @require_POST لجميع العمليات التي تغير البيانات.

---

## 3. رفع الملفات (File Upload)

### ✅ الإيجابيات
- تم تحديد حجم أقصى للملفات (15MB)
- استخدام upload_to لتنظيم الملفات
- معظم حقول الصور تستخدم ImageField

### ⚠️ المشاكل

#### 3.1 عدم التحقق من نوع الملف
**الخطورة:** 🔴 عالية
**المشكلة:** لا يوجد تحقق من نوع الملف الحقيقي (MIME type).
**التوصية:** إضافة تحقق من نوع الملف:
```python
def validate_file_type(file):
    allowed_types = ['image/jpeg', 'image/png', 'application/pdf']
    import magic
    file_type = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)
    if file_type not in allowed_types:
        raise ValidationError('نوع الملف غير مسموح')
```

#### 3.2 عدم التحقق من حجم الصورة
**الخطورة:** 🟡 متوسطة
**المشكلة:** يمكن رفع صور ضخمة تستهلك المساحة.
**التوصية:** إضافة تحقق من الأبعاد:
```python
from PIL import Image
def validate_image_size(file):
    img = Image.open(file)
    if img.width > 4000 or img.height > 4000:
        raise ValidationError('أبعاد الصورة كبيرة جداً')
```

#### 3.3 عدم إعادة تسمية الملفات
**الخطورة:** 🟡 متوسطة
**المشكلة:** أسماء الملفات الأصلية قد تحتوي على مسارات أو أحرف خاصة.
**التوصية:** إعادة تسمية الملفات:
```python
import uuid
def get_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"uploads/{filename}"
```

#### 3.4 عدم المسح الآمن للملفات
**الخطورة:** 🟡 متوسطة
**المشكلة:** عند حذف السجل، قد تبقى الملفات.
**التوصية:** استخدام signals لحذف الملفات:
```python
from django.db.models.signals import post_delete
from django.dispatch import receiver

@receiver(post_delete, sender=PropertyImage)
def delete_property_image(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(False)
```

---

## 4. حقن SQL (SQL Injection)

### ✅ الإيجابيات
- استخدام Django ORM في جميع الاستعلامات
- عدم استخدام استعلامات SQL خامة
- استخدام Q objects للبحث المعقد

### ✅ النتيجة
**لا توجد مخاطر SQL injection** - Django ORM يحمي تلقائياً.

---

## 5. هجمات XSS (Cross-Site Scripting)

### ✅ الإيجابيات
- استخدام Django templates يحمي تلقائياً
- تم استخدام textContent في chatbot JavaScript

### ⚠️ المشاكل

#### 5.1 بعض الحقول تعرض بدون escape
**الخطورة:** 🟡 متوسطة
**المشكلة:** بعض الحقول في API responses تعرض بدون escape.
**التوصية:** استخدام Django's escape:
```python
from django.utils.html import escape
response_data = {
    'title': escape(property.title),
    'description': escape(property.description)
}
```

#### 5.2 JSON responses قد تحتوي على HTML
**الخطورة:** 🟡 متوسطة
**المشكلة:** بعض API endpoints تُرجع بيانات تحتوي على HTML.
**التوصية:** إزالة HTML من responses API أو استخدام safe encoding.

---

## 6. حماية CSRF (Cross-Site Request Forgery)

### ✅ الإيجابيات
- CSRF protection مفعّل
- استخدام CSRF tokens في forms
- CSRF_TRUSTED_ORIGINS محددة

### ⚠️ المشاكل

#### 6.1 CSRF_COOKIE_HTTPONLY = False
**تم ذكره في القسم 1.4**

#### 6.2 بعض API endpoints قد تحتاج إلى حماية
**الخطورة:** 🟡 متوسطة
**المشكلة:** بعض endpoints قد لا تتحقق من CSRF بشكل صحيح.
**التوصية:** التأكد من استخدام @csrf_exempt فقط عند الضرورة القصوى.

---

## 7. تقييد المعدل (Rate Limiting)

### ✅ الإيجابيات
- REST Framework يحتوي على throttling
- تم تحديد معدلات (anon: 100/hour, user: 1000/hour)

### ⚠️ المشاكل

#### 7.1 المعدلات قد تكون عالية جداً
**الخطورة:** 🟡 متوسطة
**المشكلة:** 1000 طلب/ساعة للمستخدم قد يسبب استهلاك موارد.
**التوصية:** تقليل المعدلات:
```python
'DEFAULT_THROTTLE_RATES': {
    'anon': '30/hour',
    'user': '300/hour'
}
```

#### 7.2 لا يوجد rate limiting للـ AI endpoints
**الخطورة:** 🔴 عالية
**المشكلة:** AI endpoints مفتوحة بدون تقييد معدل.
**التوصية:** إضافة throttling مخصص:
```python
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def ai_chat(request):
```

---

## 8. إدارة الأسرار (Secret Management)

### ✅ الإيجابيات
- استخدام environment variables
- عدم تخزين الأسرار في الكود
- استخدام python-dotenv

### ⚠️ المشاكل

#### 8.1 .env file قد يكون في git
**الخطورة:** 🔴 عالية
**المشكلة:** إذا تم إضافة .env إلى git، ستكون الأسرار مكشوفة.
**التوصية:** التأكد من وجود .env في .gitignore:
```
.env
.env.local
.env.production
```

#### 8.2 عدم التحقق من قيم الأسرار
**الخطورة:** 🟡 متوسطة
**المشكلة:** لا يوجد تحقق من أن الأسرار مُوفرة.
**التوصية:** إضافة validation:
```python
if not DEBUG and not os.getenv('SECRET_KEY'):
    raise ValueError('SECRET_KEY must be set in production')
```

---

## 9. أمان قاعدة البيانات (Database Security)

### ✅ الإيجابيات
- استخدام Django ORM
- عدم استخدام raw SQL
- استخدام environment variables لاتصال قاعدة البيانات

### ⚠️ المشاكل

#### 9.1 SQLite في التطوير
**الخطورة:** 🟢 منخفضة
**المشكلة:** SQLite مناسب للتطوير فقط.
**التوصية:** استخدام PostgreSQL في جميع البيئات.

#### 9.2 عدم التشفير للبيانات الحساسة
**الخطورة:** 🟡 متوسطة
**المشكلة:** البيانات الحساسة (مثل أرقام الهواتف) مخزنة بشكل عادي.
**التوصية:** استخدام التشفير:
```python
from cryptography.fernet import Fernet
def encrypt_phone(phone):
    cipher = Fernet(settings.ENCRYPTION_KEY)
    return cipher.encrypt(phone.encode())
```

---

## 10. إدارة الجلسات (Session Management)

### ✅ الإيجابيات
- SESSION_COOKIE_HTTPONLY = True
- SESSION_COOKIE_SECURE في الإنتاج
- SESSION_COOKIE_SAMESITE = 'Lax'

### ⚠️ المشاكل

#### 10.1 SESSION_COOKIE_AGE طويل جداً
**الخطورة:** 🟡 متوسطة
```python
SESSION_COOKIE_AGE = 3600 * 24 * 7  # 7 أيام
```
**المشكلة:** الجلسة تستمر لمدة أسبوع.
**التوصية:** تقليل المدة:
```python
SESSION_COOKIE_AGE = 3600 * 24 * 2  # يومين
```

---

## 11. المصادقة والتفويض (Authentication & Authorization)

### ✅ الإيجابيات
- استخدام Django's built-in authentication
- @login_required في معظم الـ views
- @staff_required للإدارة
- password validators مفعّلة

### ⚠️ المشاكل

#### 11.1 عدم وجود Two-Factor Authentication
**الخطورة:** 🟡 متوسطة
**المشكلة:** لا يوجد 2FA للحسابات الحساسة.
**التوصية:** إضافة Django OTP أو مكتبة مشابهة.

#### 11.2 عدم وجود password history
**الخطورة:** 🟡 متوسطة
**المشكلة:** يمكن للمستخدم إعادة استخدام كلمات المرور القديمة.
**التوصية:** إضافة Django Password History أو تطبيق custom validator.

---

## 12. السجلات والتدقيق (Logging & Auditing)

### ✅ الإيجابيات
- نظام logging مُطبق
- rotation of log files
- logging للـ AI requests

### ⚠️ المشاكل

#### 12.1 عدم وجود audit trail للعمليات الحساسة
**الخطورة:** 🟡 متوسطة
**المشكلة:** لا يوجد سجل للعمليات الحساسة (حذف، تعديل).
**التوصية:** إضافة audit logging:
```python
from django.contrib.admin.models import LogEntry
LogEntry.objects.log_action(
    user_id=request.user.id,
    content_type_id=ContentType.objects.get_for_model(obj).id,
    object_id=obj.id,
    object_repr=str(obj),
    action_flag=CHANGE
)
```

#### 12.2 عدم وجود logging للعمليات الفاشلة
**الخطورة:** 🟡 متوسطة
**المشكلة:** لا يوجد logging لمحاولات تسجيل الدخول الفاشلة.
**التوصية:** إضافة logging لمحاولات تسجيل الدخول.

---

## 13. النسخ الاحتياطي (Backup)

### ⚠️ المشاكل

#### 13.1 عدم وجود استراتيجية نسخ احتياطي واضحة
**الخطورة:** 🔴 عالية
**المشكلة:** لا يوجد ذكر لاستراتيجية النسخ الاحتياطي.
**التوصية:** إضافة:
- النسخ الاحتياطي اليومي لقاعدة البيانات
- النسخ الاحتياطي للملفات المرفوعة
- التشفير للنسخ الاحتياطية
- اختبار الاستعادة بشكل دوري

---

## 14. HTTPS و SSL/TLS

### ✅ الإيجابيات
- SECURE_SSL_REDIRECT قابل للتفعيل
- SECURE_PROXY_SSL_HEADER مُطبق
- HSTS مُطبق في الإنتاج

### ⚠️ المشاكل

#### 14.1 SECURE_SSL_REDIRECT افتراضياً False
**الخطورة:** 🟡 متوسطة
```python
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
```
**المشكلة:** يجب أن يكون True في الإنتاج.
**التوصية:** تغيير القيمة الافتراضية:
```python
SECURE_SSL_REDIRECT = not DEBUG
```

---

## 15. العناوين والتعليقات (Headers & Comments)

### ✅ الإيجابيات
- X-Frame-Options: DENY
- SECURE_BROWSER_XSS_FILTER
- SECURE_CONTENT_TYPE_NOSNIFF

### ⚠️ المشاكل

#### 15.1 عدم وجود Content-Security-Policy
**الخطورة:** 🟡 متوسطة
**المشكلة:** لا يوجد CSP header.
**التوصية:** إضافة CSP:
```python
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ["'self'"],
    'script-src': ["'self'", 'https://cdn.jsdelivr.net'],
    'style-src': ["'self'", 'https://cdn.jsdelivr.net'],
    'img-src': ["'self'", 'data:', 'https:'],
}
```

---

## التوصيات الأولوية

### 🔴 عالية الأولوية (حرجة)
1. تغيير DEBUG default إلى False
2. إضافة تحقق من نوع الملف في رفع الملفات
3. إضافة rate limiting للـ AI endpoints
4. التأكد من أن .env في .gitignore
5. إضافة استراتيجية نسخ احتياطي
6. تفعيل SECURE_SSL_REDIRECT في الإنتاج

### 🟡 متوسطة الأولوية
1. إزالة '*' من ALLOWED_HOSTS
2. تفعيل CSRF_COOKIE_HTTPONLY
3. تقليل SESSION_COOKIE_AGE
4. تقليل معدلات rate limiting
5. إضافة Content-Security-Policy
6. إضافة audit logging
7. تشفير البيانات الحساسة في قاعدة البيانات
8. إضافة Two-Factor Authentication

### 🟢 منخفضة الأولوية
1. إضافة password history
2. إضافة validation لأبعاد الصور
3. إعادة تسمية الملفات المرفوعة
4. إضافة logging لمحاولات تسجيل الدخول الفاشلة
5. تحسين escape في API responses

---

## الخلاصة

المشروع يحتوي على إطار أمني جيد بشكل عام، مع استخدام Django الميزات الأمنية المدمجة. ومع ذلك، هناك عدة مجالات تحتاج إلى تحسين، خاصة في:

1. **إدارة الأسرار وتكوين الإنتاج**
2. **رفع الملفات والتحقق من الأنواع**
3. **تقييد المعدل للـ AI endpoints**
4. **النسخ الاحتياطي والاستعادة**
5. **التدقيق والسجلات**

من خلال تنفيذ التوصيات المذكورة أعلاه، يمكن تحسين أمان المشروع بشكل كبير.

---

**التقرير أُعد بواسطة:** مهندس أمن معلومات
**التاريخ:** 2026-08-15
**الإصدار:** 1.0
