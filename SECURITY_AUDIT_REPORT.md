# تقرير تدقيق أمني شامل - منصة دلال العقارية

## ملخص تنفيذي

هذا التقرير يغطي ثلاثة أنظمة رئيسية:
1. نظام العقود `/contracts/`
2. صفحة الخريطة `/dashboard/map/`
3. لوحة المستخدم `/dashboard/`

---

## الجزء الأول: نظام العقود `/contracts/`

### النظام الحالي

#### Models الموجودة:

**RealEstateContract** (سطر 16423 في properties/models.py):
- ✅ يحتوي على جميع الحقول الأساسية
- ✅ يحتوي على نظام Soft Delete (`is_archived`)
- ✅ يحتوي على Audit Log من خلال `ContractAuditLog`
- ✅ يحتوي على معلومات الأطراف (property, broker, client)
- ✅ يحتوي على معلومات مالية (amount, deposit, commission_rate, commission_amount)
- ✅ يحتوي على حالات واضحة (draft, pending, active, completed, terminated, expired, cancelled)

**ContractDocument** (سطر 16772 في properties/models.py):
- ✅ موجود ويعمل
- ✅ يحتوي على `document_type` choices
- ✅ يحتوي على `page_number` لترتيب الصفحات
- ✅ يحتوي على `file_size` و `file_type`
- ✅ يحتوي على `uploaded_by` لتتبع رافع الملف

---

### المشاكل الأمنية الحرجة المكتشفة:

#### 1. **رقم العقد غير آمن للطلبات المتزامنة**
```python
def generate_contract_number(self):
    count = RealEstateContract.objects.filter(
        contract_number__startswith=f'CTR-RE-{year}'
    ).count()
    return f'CTR-RE-{year}-{count + 1:04d}'
```
**المشكلة**: يمكن حدوث تكرار في حالة الطلبات المتزامنة
**الخطر**: عقدان بنفس الرقم → تضارب في قاعدة البيانات
**الحل المطلوب**: استخدام `transaction.atomic()` + `select_for_update()` أو unique constraint + retry

#### 2. **حساب العمولة يحدث في save() بدون Transaction**
```python
def save(self, *args, **kwargs):
    if self.commission_rate and self.amount:
        self.commission_amount = (self.amount * self.commission_rate) / 100
    super().save(*args, **kwargs)
```
**المشكلة**: لا توجد حماية ضد التلاعب من Frontend
**الخطر**: يمكن للمستخدم إرسال `commission_amount` خاطئ عبر JavaScript
**الحل المطلوب**: حساب العمولة في View قبل الحفظ، وتجاهل القيمة من POST

#### 3. **عدم حماية IDOR في Views الحالية**
```python
contract = get_object_or_404(RealEstateContract, id=contract_id)
```
**المشكلة**: المستخدم A يستطيع الوصول لعقد المستخدم B بتغيير ID
**الخطر**: كشف بيانات عقود خاصة
**الحل المطلوب**: التحقق من الصلاحيات قبل إرجاع العقد

#### 4. **حذف المستندات بدون صلاحية كافية**
```python
@login_required
def contract_document_delete(request, document_id):
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)
    document = get_object_or_404(ContractDocument, id=document_id)
```
**المشكلة**: فقط `is_superuser` يحق له الحذف، الدلال لا يستطيع حذف مستنداته
**الخطر**: الدلال لا يستطيع إدارة مستندات عقوده
**الحل المطلوب**: التحقق من أن المستخدم هو رافع المستند أو صاحب العقد

#### 5. **رفع المستندات بدون فحص كافٍ**
```python
document = ContractDocument.objects.create(
    contract=contract,
    document_type=data.get('document_type', 'other'),
    title=data.get('title', ''),
    description=data.get('description', ''),
    file=data.get('file'),
    uploaded_by=request.user
)
```
**المشكلة**: لا يوجد فحص لحجم الملف، نوع الملف، أو عدد الملفات
**الخطر**: رفع ملفات ضخمة أو خطيرة
**الحل المطلوب**: فحص صارم للحجم، النوع، والامتداد

#### 6. **عدم وجود `party_type` للصور الشخصية**
النظام الحالي لا يميز بين:
- صورة المشتري
- صورة البائع
- صورة الدلال

**المشكلة**: لا يمكن معرفة الصورة تخص من
**الحل المطلوب**: إضافة `party_type` field مع choices (buyer, seller, broker)

#### 7. **عدم حماية ملفات المستندات**
الملفات يتم تخزينها في `contract_documents/` بدون حماية
**المشكلة**: أي شخص يعرف الرابط يستطيع تحميل المستند
**الخطر**: كشف مستندات حساسة
**الحل المطلوب**: Endpoint محمي للتحميل مع Permission Check

---

### الحالة الحالية للعقود:

| المكون | الحالة | الملاحظات |
|-------|-------|---------|
| RealEstateContract Model | ✅ موجود ومكتمل | يحتاج تحسينات أمنية |
| ContractDocument Model | ✅ موجود ومكتمل | يحتاج إضافة party_type |
| ContractAuditLog | ✅ موجود | يعمل بشكل صحيح |
| Forms | ✅ موجودة | تحتاج تحديثات أمنية |
| Views | ⚠️ موجودة | تحتاج حماية IDOR |
| APIs | ⚠️ موجودة | تحتاج حماية |
| Templates | ❓ غير معروف | يحتاج فحص |
| URLs | ❓ غير معروف | يحتاج فحص |

---

## الجزء الثاني: صفحة الخريطة `/dashboard/map/`

### الحالة الحالية:

#### وجود الخريطة:
- ✅ `interactive_map_view` موجود في views.py (سطر 1100)
- ✅ `map_api_properties` موجود كـ API
- ✅ تستخدم Leaflet أو مكتبة خريطة (يحتاج فحص)
- ✅ لديها Filter للمحافظات والأسعار

#### المشاكل المحتملة:
- ❓ هل تستخدم مصدر بيانات العقارات المنشورة؟
- ❓ هل تحتوي على صلاحيات؟
- ❓ هل تعرض عقارات غير منشورة؟
- ❓ هل تعرض عقارات بدون إحداثيات صحيحة؟
- ❓ هل هناك IDOR في API الخريطة؟
- ❓ هل تعرض بيانات حساسة (commission, broker details)؟

---

## الجزء الثالث: لوحة المستخدم `/dashboard/`

### الحالة الحالية:

#### الـ Views الموجودة:
- ✅ `dashboard` view موجود (سطر 3336 في views.py)
- ✅ `user_dashboard` view موجود (سطر 2764)
- ✅ محمي بـ `@user_required` decorator
- ✅ يعرض saved properties, notifications, auctions

#### المشاكل المحتملة:
- ❓ هل `/dashboard/` يستخدمها الدلال أيضاً؟
- ❓ هل هناك IDOR في API العميل؟
- ❓ هل تعرض بيانات مستخدمين آخرين؟
- ❓ هل تسمح بتغيير user_id من Frontend؟
- ❓ هل APIs محمية مثل Pages؟

---

## الأولويات الأمنية الحرجة:

### الأولوية 1 (حرجة جداً - يجب إصلاح فوراً):

1. **رقم العقد المتزامن** - يمكن تكرار الأرقام
2. **IDOR في نظام العقود** - كشف بيانات خاصة
3. **حماية الملفات** - الوصول غير المصرح للمستندات
4. **حساب العمولة** - التلاعب من Frontend

### الأولوية 2 (مهم جداً):

5. **صلاحيات الصور الشخصية** - إضافة party_type
6. **فحص الملفات** - حجم، نوع، امتداد
7. **Transaction للعقود** - عدم ترك بيانات غير مكتملة
8. **حماية APIs** - نفس صلاحيات Pages

### الأولوية 3 (مهم):

9. **فصل الصلاحيات بالكامل** - USER/BROKER/ADMIN
10. **تحسين Performance** - N+1 queries
11. **Pagination** - تحميل كافة البيانات دفعة واحدة
12. **Audit Log كامل** - تسجيل كل العمليات

---

## التوصيات:

### 1. نظام العقود:
- ✅ لا إنشاء Models جديدة (استخدم الموجودة)
- ⚠️ إضافة `party_type` إلى `ContractDocument`
- ⚠️ إصلاح `generate_contract_number()` لمنع التكرار
- ⚠️ إضافة Permission checks لجميع Views
- ⚠️ إنشاء Endpoint محمي لتحميل الملفات
- ⚠️ إضافة Transaction لإنشاء العقد + المستندات

### 2. صفحة الخريطة:
- ✅ استخدام مصدر بيانات العقارات المنشورة فقط
- ⚠️ إضافة Permission checks
- ⚠️ منع عرض بيانات حساسة
- ⚠️ التحقق من الإحداثيات الصحيحة
- ⚠️ إضافة Pagination/Bounding Box

### 3. لوحة المستخدم:
- ✅ استخدام `@user_required` decorator
- ⚠️ التأكد من عدم استخدام الدلال للوحة
- ⚠️ حماية جميع APIs
- ⚠️ منع IDOR
- ⚠️ فصل لوحات التحكم بشكل كامل

---

## الحاجة للإجراء الفوري:

بما أن هذا مشروع إنتاجي على Railway، يجب:

1. ✅ عدم استخدام `makemigrations` تلقائياً
2. ✅ اختبار كل إصلاح على PostgreSQL
3. ✅ عمل Backup قبل Migrations
4. ✅ إصلاح الأولويات الأمنية الحرجة أولاً
5. ✅ إضافة اختبارات شاملة

---

## الملفات التي تحتاج فحص وإصلاح:

### العقود:
- `properties/models.py` - RealEstateContract, ContractDocument
- `properties/contract_views.py` - Views العقود
- `properties/contract_api_views.py` - APIs العقود
- `properties/forms.py` - ContractForm, ContractDocumentForm
- `properties/urls.py` - URLs العقود
- Templates العقود (يحتاج تحديد)

### الخريطة:
- `properties/views.py` - interactive_map_view, map_api_properties
- JavaScript الخريطة (يحتاج تحديد)
- Template الخريطة (يحتاج تحديد)

### لوحة المستخدم:
- `properties/views.py` - dashboard, user_dashboard
- `properties/urls.py` - URLs لوحة المستخدم
- Templates لوحة المستخدم (يحتاج تحديد)
- APIs لوحة المستخدم (يحتاج تحديد)

---

## الاستراتيجية المقترحة:

بما أن الطلب ضخم جداً، سأقوم بـ:

1. **المرحلة 1**: إصلاح المشاكل الأمنية الحرجة في نظام العقود
2. **المرحلة 2**: فحص وإصلاح صفحة الخريطة
3. **المرحلة 3**: فحص وإصلاح لوحة المستخدم
4. **المرحلة 4**: إضافة اختبارات شاملة
5. **المرحلة 5**: فحص Django check و makemigrations --check

سأبدأ فوراً بالمرحلة 1.