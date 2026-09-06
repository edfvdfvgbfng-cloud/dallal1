# Migrations Audit Report
## تدقيق شامل لعمليات Migrations

### 📅 تاريخ التقرير
2026-09-06

### 🔍 ملخص النتائج

**إجمالي Migrations:** 227 migration file

**العمليات التدميرية المكتشفة:**
- DeleteModel: 6 حالات
- RunPython: 9 حالات
- RunSQL: 0 حالات

### 📊 التحليل التفصيلي

#### 1. DeleteModel Operations (6 حالات)

##### الحالة 1: UserSettings ( migrations 0025, 0026, 0027 )

**السياق:**
- 0025_delete_usersettings.py: No-op migration
- 0026_delete_usersettings.py: delete_usersettings_if_exists function
- 0027_delete_usersettings.py: DROP TABLE properties_usersettings

**تحليل 0027_delete_usersettings.py:**
```python
def drop_usersettings_table_if_exists(apps, schema_editor):
    """Drop UserSettings table only when it exists (handles partial migration history)."""
    table_names = connection.introspection.table_names()
    if 'properties_usersettings' in table_names:
        schema_editor.execute('DROP TABLE "properties_usersettings"')
```

**التقييم:** ⚠️ تدميري لكن محمي
- يتحقق من وجود الجدول قبل الحذف
- يستخدم DROP TABLE مباشرة
- قد يكون مقصود لإزالة UserSettings القديمة
- **التوصية:** مراجعة إذا UserSettings لا تزال مستخدمة

##### الحالة 2: ChannelContentShare ( migration 0097 )

**السياق:**
```python
migrations.DeleteModel(name='ChannelContentShare'),
```

**التقييم:** ⚠️ تدميري
- حذف Model مباشر
- قد يكون مقصود لإزالة feature غير مستخدم
- **التوصية:** مراجعة إذا ChannelContentShare لا تزال مستخدمة

##### الحالة 3: ResortImage ( migration 0097 )

**السياق:**
```python
migrations.DeleteModel(name='ResortImage'),
```

**التقييم:** ⚠️ تدميري
- حذف Model مباشر
- قد يكون مقصود لاستبدالها بـ Resort Gallery
- **التوصية:** مراجعة إذا ResortImage لا تزال مستخدمة

##### الحالة 4: PushSubscription ( migration 0223 )

**السياق:**
```python
migrations.DeleteModel(name='PushSubscription'),
```

**التقييم:** ⚠️ تدميري
- حذف Model مباشر
- قد يكون مقصود لإزالة feature غير مستخدم
- **التوصية:** مراجعة إذا PushSubscription لا تزال مستخدمة

##### الحالة 5: TravelCompanyPost ( migration 0223 )

**السياق:**
```python
migrations.DeleteModel(name='TravelCompanyPost'),
```

**التقييم:** ⚠️ تدميري
- حذف Model مباشر
- قد يكون مقصود لإزالة feature غير مستخدم
- **التوصية:** مراجعة إذا TravelCompanyPost لا تزال مستخدمة

##### الحالة 6: TravelCompanyPostImage ( migration 0223 )

**السياق:**
```python
migrations.DeleteModel(name='TravelCompanyPostImage'),
```

**التقييم:** ⚠️ تدميري
- حذف Model مباشر
- قد يكون مقصود لإزالة feature غير مستخدم
- **التوصية:** مراجعة إذا TravelCompanyPostImage لا تزال مستخدمة

#### 2. RunPython Operations (9 حالات)

##### الحالة 1: ensure_superuser ( migration 0192 )

**السياق:**
```python
migrations.RunPython(ensure_superuser, reverse_ensure_superuser),
```

**التقييم:** ✅ آمن
- يخلق superuser إذا لم يكن موجود
- لا يحذف بيانات
- **التوصية:** آمن للإنتاج

##### الحالة 2: create_model_if_not_exists ( migration 0068 )

**السياق:**
```python
migrations.RunPython(create_model_if_not_exists, migrations.RunPython.noop),
```

**التقييم:** ✅ آمن
- يخلق model إذا لم يكن موجود
- لا يحذف بيانات
- **التوصية:** آمن للإنتاج

##### الحالة 3: create_superuser ( migration 0055 )

**السياق:**
```python
migrations.RunPython(create_superuser, reverse_create_superuser),
```

**التقييم:** ✅ آمن
- يخلق superuser
- لا يحذف بيانات
- **التوصية:** آمن للإنتاج

##### الحالة 4: drop_usersettings_table_if_exists ( migration 0027 )

**السياق:**
```python
migrations.RunPython(drop_usersettings_table_if_exists, migrations.RunPython.noop),
```

**التقييم:** ⚠️ تدميري
- يحذف جدول UserSettings
- **التوصية:** مراجعة إذا UserSettings لا تزال مستخدمة

##### الحالة 5: delete_usersettings_if_exists ( migration 0026 )

**السياق:**
```python
migrations.RunPython(delete_usersettings_if_exists, migrations.RunPython.noop),
```

**التقييم:** ⚠️ تدميري
- يحذف UserSettings data
- **التوصية:** مراجعة إذا UserSettings لا تزال مستخدمة

##### الحالة 6: noop ( migration 0025 )

**السياق:**
```python
migrations.RunPython(noop, migrations.RunPython.noop),
```

**التقييم:** ✅ آمن
- لا يفعل شيئاً
- **التوصية:** آمن للإنتاج

##### الحالة 7: delete_usersettings_if_exists ( migration 0018 )

**السياق:**
```python
migrations.RunPython(delete_usersettings_if_exists, migrations.RunPython.noop, atomic=False),
```

**التقييم:** ⚠️ تدميري
- يحذف UserSettings data
- **التوصية:** مراجعة إذا UserSettings لا تزال مستخدمة

##### الحالة 8: populate_property_slugs ( migration 0004 )

**السياق:**
```python
migrations.RunPython(populate_property_slugs, migrations.RunPython.noop),
```

**التقييم:** ✅ آمن
- يملأ slug fields
- لا يحذف بيانات
- **التوصية:** آمن للإنتاج

#### 3. Migration Conflict الحالي

**المشكلة:**
```
relation "properties_property_slug_f3b16024_like" already exists
```

**السبب:**
- Migration 0004 يحاول إنشاء index
- Index موجود بالفعل في database
- قد يكون من محاولة نشر سابقة

**الحل المقترح:**
1. استخدام `python manage.py showmigrations` لفحص الحالة
2. استخدام `python manage.py migrate --plan` لرؤية ما سيتم تنفيذه
3. إذا Index موجود والschema مطابق:
   - استخدام `migrate --fake` للمigration المتضارب
4. إذا schema غير مطابق:
   - حذف Index المتضارب يدوياً
   - إعادة تشغيل migrate

### 🚨 التوصيات الحرجة

#### 1. قبل Production Deploy

**فحص UserSettings:**
- [ ] هل UserSettings لا تزال مستخدمة في code؟
- [ ] هل يوجد بيانات في UserSettings table؟
- [ ] هل حذف UserSettings مقصود؟

**فحص Models المحذوفة:**
- [ ] هل ChannelContentShare لا تزال مستخدمة؟
- [ ] هل ResortImage لا تزال مستخدمة؟
- [ ] هل PushSubscription لا تزال مستخدمة؟
- [ ] هل TravelCompanyPost لا تزال مستخدمة؟
- [ ] هل TravelCompanyPostImage لا تزال مستخدمة؟

**فحص Migration Conflict:**
- [ ] showmigrations تم
- [ ] migrate --plan تم
- [ ] النتيجة مراجعة
- [ ] الحل المحدد

#### 2. أثناء Production Deploy

**قبل تشغيل migrate:**
- [ ] Backup PostgreSQL
- [ ] فحص DATABASE_URL
- [ ] تأكد من Volume الصحيح
- [ ] migrate --plan مراجعة

**أثناء تشغيل migrate:**
- [ ] استخدام --noinput
- [ ] مراقبة الأخطاء
- [ ] لا تستخدم --fake بدون سبب موثق

**بعد تشغيل migrate:**
- [ ] فحص showmigrations
- [ ] فحص database schema
- [ ] تأكد من أن البيانات موجودة

### 📋 Checklist Migrations Safety

- [ ] جميع migrations موجودة ✅
- [ ] لا توجد migrations مفقودة ✅
- [ ] DeleteModel Operations مراجعة ⚠️
- [ ] RunPython Operations مراجعة ⚠️
- [ ] RunSQL Operations غير موجودة ✅
- [ ] Migration Conflict محلول ❌
- [ ] migrate --plan مراجعة ❌
- [ ] Backup قبل migrate ❌
- [ ] UserSettings مراجعة ❌
- [ ] Models المحذوفة مراجعة ❌

### 🔒 الحماية الحالية

- ✅ لا يوجد RunSQL تدميري
- ✅ معظم RunPython آمنة
- ✅ DeleteModel لديها context
- ⚠️ UserSettings deletion يحتاج مراجعة
- ⚠️ Models المحذوفة تحتاج مراجعة
- ❌ Migration conflict غير محلول

### 🎯 الخطوات التالية

1. **فوري:** مراجعة UserSettings usage
2. **فوري:** مراجعة Models المحذوفة
3. **فوري:** حل migration conflict
4. **قبل Production:** migrate --plan
5. **قبل Production:** Backup PostgreSQL
6. **قبل Production:** فحص showmigrations

### ⚠️ قاعدة ذهبية

**لا تشغل migrate على Production قبل:**
1. Backup PostgreSQL
2. مراجعة migrate --plan
3. حل جميع conflicts
4. تأكد من DATABASE_URL الصحيح
5. تأكد من Volume الصحيح