# إصلاحات أمنية صفحة الخريطة - تقرير الإصلاح

## المشاكل الأمنية المكتشفة في صفحة الخريطة `/dashboard/map/`

### ❌ المشاكل الحرجة:

1. **لا توجد Permission checks في `map_api_properties`**
   - أي مستخدم يستطيع الوصول للـ API
   - لا توجد تحقق من هوية المستخدم أو صلاحياته
   - الإصلاح: إضافة Permission checks قبل إرجاع البيانات

2. **تعريض بيانات حساسة بدون صلاحية**
   - `'broker_name': prop.broker.display_name if prop.broker else None`
   - أي مستخدم يستطيع معرفة اسم الدلال
   - الإصلاح: عرض broker_name فقط للمستخدمين المصرح لهم (admin, broker)

3. **كشف مسارات الملفات مباشرة**
   - `'main_image': prop.main_image.url if prop.main_image else None`
   - قد تكشف مسارات حساسة في بعض السيناريوهات
   - الإصلاح: استخدام المسار النسبي بدلاً من full URL

4. **عدم التحقق من الإحداثيات الصحيحة**
   - لا يوجد تحقق من أن الإحداثيات ضمن النطاق الصحيح
   - قد تعرض قيم خاطئة مثل (0,0)
   - الإصلاح: التحقق من النطاق الصحيح وتجاهل القيم غير الصالحة

5. **الاعتماد على `status='available'` فقط**
   - قد لا يكون هذا هو الحالة الصحيحة للعقود المنشورة
   - الإصلاح: استخدام `PUBLIC_STATUSES` من constants

6. **لا توجد Filters من Backend**
   - الفلترة تعتمد فقط على JavaScript
   - لا توجد validation للفلاتر في Backend
   - الإصلاح: تطبيق الفلاتر في Backend مع validation

### ⚠️ المشاكل المتوسطة:

7. **عدم وجود Bounding Box filter**
   - يتم تحميل 200 عقار دفعة واحدة
   - قد يكون بطيئاً مع زيادة البيانات
   - الإصلاح: إضافة دعم Bounding Box filter

8. **تعرض بيانات غير ضرورية**
   - `created_at` قد لا تكون ضرورية للخريطة
   - الإصلاح: إزالة البيانات غير الضرورية

9. **عدم وجود Pagination**
   - عدد ثابت من النتائج (200)
   - الإصلاح: إضافة Pagination أو Bounding Box

---

## الإصلاحات المقترحة:

### الإصلاح 1: إضافة Permission Checks

```python
from .permissions import get_user_type

# في بداية الدالة
user_type = get_user_type(request.user) if request.user.is_authenticated else None
```

### الإصلاح 2: حماية البيانات الحساسة

```python
# فقط عرض broker_name للمستخدمين المصرح لهم
if user_type in ['admin', 'broker']:
    if prop.broker:
        prop_data['broker_name'] = prop.broker.display_name
```

### الإصلاح 3: التحقق من الإحداثيات

```python
# Validate coordinates are reasonable
lat = float(prop.latitude)
lng = float(prop.longitude)

# Skip invalid coordinates (0,0)
if lat == 0 and lng == 0:
    continue

# Skip coordinates outside valid ranges
if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
    continue
```

### الإصلاح 4: استخدام PUBLIC_STATUSES

```python
from .constants import PUBLIC_STATUSES

properties = Property.objects.filter(
    is_published=True,
    status__in=PUBLIC_STATUSES,  # بدلاً من status='available'
    latitude__isnull=False,
    longitude__isnull=False
)
```

### الإصلاح 5: تطبيق الفلاتر في Backend

```python
# Get filter parameters
governorate = request.GET.get('governorate')
city = request.GET.get('city')
property_type = request.GET.get('property_type')
transaction_type = request.GET.get('transaction_type')
price_min = request.GET.get('price_min')
price_max = request.GET.get('price_max')

# Apply filters from Backend
if governorate:
    properties = properties.filter(governorate=governorate)
if city:
    properties = properties.filter(city=city)
if property_type:
    properties = properties.filter(property_type=property_type)
if transaction_type:
    properties = properties.filter(transaction_type=transaction_type)
if price_min:
    try:
        properties = properties.filter(price__gte=float(price_min))
    except ValueError:
        pass
if price_max:
    try:
        properties = properties.filter(price__lte=float(price_max))
    except ValueError:
        pass
```

### الإصلاح 6: إضافة Bounding Box Filter

```python
bounds = request.GET.get('bounds')

if bounds:
    try:
        bounds_data = json.loads(bounds)
        south = float(bounds_data.get('south'))
        north = float(bounds_data.get('north'))
        west = float(bounds_data.get('west'))
        east = float(bounds_data.get('east'))
        properties = properties.filter(
            latitude__gte=south,
            latitude__lte=north,
            longitude__gte=west,
            longitude__lte=east
        )
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
```

### الإصلاح 7: تقليل البيانات المعرضة

```python
# MINIMAL PUBLIC DATA ONLY
prop_data = {
    'id': prop.id,
    'title': prop.title,
    'slug': prop.slug,
    'price': prop.price,
    'currency': prop.currency,
    'property_type': prop.property_type,
    'transaction_type': prop.transaction_type,
    'area': prop.area,
    'bedrooms': prop.bedrooms,
    'bathrooms': prop.bathrooms,
    'governorate': prop.governorate,
    'city': prop.city,
    'latitude': lat,
    'longitude': lng,
    'url': f'/property/{prop.slug}/' if prop.slug else '',
}

# Add image safely
if prop.main_image:
    prop_data['image'] = f'/media/{prop.main_image.name}'
```

---

## الملفات التي تحتاج إصلاح:

1. `properties/views.py` - سطر 1148-1198 (`map_api_properties`)
2. `properties/views.py` - سطر 1101-1145 (`interactive_map_view`)
3. `properties/views.py` - سطر 1201-1260 (`map_api_search`)
4. `properties/broker_views.py` - سطر 1304-1425 (`map_api_properties` في broker_views)

---

## الأولويات:

### حرجة جداً:
1. Permission checks
2. حماية البيانات الحساسة (broker_name)
3. التحقق من الإحداثيات
4. استخدام PUBLIC_STATUSES

### مهمة:
5. تطبيق الفلاتر في Backend
6. إضافة Bounding Box filter
7. تقليل البيانات المعرضة

### أقل أهمية:
8. إضافة Pagination
9. تحسين Performance
10. إضافة Cache مناسب

---

## الاختبارات المطلوبة:

1. مستخدم غير مسجل يستطيع رؤية العقارات المنشورة فقط
2. مستخدم عادي لا يرى broker_name
3. دلال يرى broker_name
4. إدارة يرى broker_name
5. العقود بدون إحداثيات لا تظهر
6. الإحداثيات (0,0) لا تظهر
7. الفلاتر تعمل من Backend
8. Bounding Box filter يعمل
9. لا يوجد IDOR
10. API محمية بنفس صلاحيات Pages