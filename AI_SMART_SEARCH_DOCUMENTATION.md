# 🤖 AI SMART ASSISTANT DOCUMENTATION

**تاريخ التوثيق:** 2026-08-27  
**المشروع:** دلال - منصة عقارية Django  
**الإصدار:** 1.0.0

---

## 📋 نظرة عامة

المساعد الذكي هو نظام متكامل للبحث والتوجيه الذكي داخل منصة دلال. يستخدم نظام AI لفهم طلبات المستخدم باللغة العربية والإنجليزية، ويجمع المعلومات الناقصة تدريجياً، ويبحث في قاعدة البيانات الفعلية، ويعرض النتائج المطابقة مع توجيه المستخدم إلى الإجراءات المناسبة.

---

## 🏗️ البنية المعمارية

### المكونات الرئيسية

```
User Input
    ↓
AI Smart Assistant API
    ↓
Smart Conversation Manager
    ↓
Intent Detection System
    ↓
AI Request Parser
    ↓
Validation Layer
    ↓
AI Search Service
    ↓
Django ORM
    ↓
Database
    ↓
Result Renderer
    ↓
Formatted Cards
    ↓
Frontend Display
```

### الملفات الرئيسية

1. **`ai_intent_detection.py`** - نظام اكتشاف النوايا
2. **`ai_request_parser.py`** - محلل الطلبات
3. **`ai_search_service.py`** - خدمة البحث الموحدة
4. **`ai_smart_conversation_manager.py`** - مدير المحادثات الذكي
5. **`ai_result_renderer.py`** - معالج عرض النتائج
6. **`ai_smart_assistant_api.py`** - واجهة API
7. **`ai_smart_assistant.html`** - واجهة المستخدم
8. **`ai_smart_assistant.css`** - التنسيقات
9. **`ai_smart_assistant.js`** - JavaScript client
10. **`tests_ai_smart_assistant.py`** - الاختبارات الشاملة

---

## 🔍 Intent Detection System

### النوايا المدعومة

#### النوايا العقارية
- `BUY_PROPERTY` - شراء عقار
- `SELL_PROPERTY` - بيع عقار
- `RENT_PROPERTY` - إيجار عقار
- `SEARCH_PROPERTY` - بحث عام عن عقارات

#### النوايا السياحية
- `SEARCH_HOTEL` - البحث عن فنادق
- `SEARCH_RESORT` - البحث عن منتجعات

#### نوايا الوظائف
- `SEARCH_JOB` - البحث عن وظائف
- `POST_JOB` - نشر وظيفة

#### نوايا الخدمات
- `SEARCH_SERVICE` - البحث عن خدمات
- `POST_SERVICE` - نشر خدمة

#### نوايا المزادات
- `SEARCH_AUCTION` - البحث عن مزادات

#### نوايا الدلالين
- `CONTACT_BROKER` - التواصل مع دلال
- `SEARCH_BROKER` - البحث عن دلال

#### النوايا العامة
- `GENERAL_QUESTION` - سؤال عام
- `GREETING` - تحية
- `CLEAR_CONVERSATION` - بدء محادثة جديدة
- `HELP` - طلب مساعدة

### دعم اللهجة العراقية

النظام يدعم صيغ متعددة من اللهجة العراقية:

**للشراء:**
- "أريد اشتري"
- "أريد أشتري"
- "أريد شراء"
- "بدي اشتري"
- "أدور على"

**للبيع:**
- "أريد بيع"
- "أريد أبيع"
- "بدي بيع"

**للمواقع:**
- "الناصرية" → "Nasiriyah"
- "بغداد" → "Baghdad"
- "البصرة" → "Basra"
- "أربيل" → "Erbil"

**للأسعار:**
- "150 مليون" → 150,000,000 IQD
- "100 ألف دولار" → 100,000 USD

---

## 📝 AI Request Parser

### استخراج الفلاتر

يقوم المحلل باستخراج الفلاتر التالية من كلام المستخدم:

#### فلاتر العقارات
- `property_type` - نوع العقار (بيت، شقة، فيلا، إلخ)
- `location` - الموقع (المحافظة/المدينة)
- `price` - السعر (القيمة والعملة)
- `area` - المساحة (متر مربع)
- `rooms` - عدد الغرف
- `purpose` - الغرض (بيع، إيجار، استثمار)
- `location_type` - نوع الموقع (داخل/خارج العراق)

#### فلاتر الفنادق
- `city` - المدينة
- `guests` - عدد الضيوف
- `star_rating` - تصنيف النجوم
- `price` - السعر

#### فلاتر المنتجعات
- `city` - المدينة
- `capacity` - السعة
- `family_suitable` - مناسب للعائلات
- `price` - السعر

#### فلاتر الوظائف
- `location` - الموقع
- `job_title` - المسمى الوظيفي
- `salary` - الراتب

#### فلاتر الخدمات
- `location` - الموقع
- `service_type` - نوع الخدمة
- `price` - السعر

#### فلاتر المزادات
- `location` - الموقع
- `property_type` - نوع العقار
- `max_bid` - أقصى مزايدة

### التحقق من الصحة

يقوم النظام بالتحقق من صحة الفلاتر المستخرجة:

- التحقق من أن السعر رقم موجب
- التحقق من أن المساحة رقم موجب
- التحقق من أن عدد الغرف عدد صحيح موجب
- التحقق من أن العملة مدعومة

---

## 🔎 AI Search Service

### خدمة البحث الموحدة

تخدم `AISearchService` كنقطة موحدة للبحث في جميع أنواع المحتوى:

```python
ai_search_service.search(intent, filters, user_id)
```

### أنواع البحث المدعومة

1. **بحث العقارات** - بحث في `Property` model
2. **بحث الفنادق** - بحث في `Hotel` model
3. **بحث المنتجعات** - بحث في `ResortInsideIraq` و `ResortOutsideIraq`
4. **بحث الوظائف** - بحث في `Job` model
5. **بحث الخدمات** - بحث في `ServiceAdvertisement` model
6. **بحث المزادات** - بحث في `Auction` model
7. **بحث الدلالين** - بحث في `Broker` model

### خوارزمية المطابقة

يستخدم النظام خوارزمية مطابقة مرجحة:

#### مطابقة العقارات
- الموقع: 30%
- السعر: 25%
- نوع العقار: 15%
- المساحة: 10%
- الغرف: 10%
- الغرض: 10%

#### مطابقة الفنادق
- الموقع: 40%
- الضيوف: 30%
- النجوم: 20%
- السعر: 10%

#### مطابقة المنتجعات
- الموقع: 40%
- السعة: 30%
- مناسبة العائلات: 20%
- السعر: 10%

#### مطابقة الوظائف
- الموقع: 40%
- المسمى الوظيفي: 30%
- الراتب: 30%

#### مطابقة الخدمات
- الموقع: 50%
- نوع الخدمة: 30%
- السعر: 20%

### حدود النتائج

- الحد الأقصى للنتائج: 10 نتائج لكل بحث
- يمكن طلب المزيد من خلال "اقتراحات قريبة"

---

## 💬 Smart Conversation Manager

### إدارة حالة المحادثة

يقوم `SmartConversationManager` بإدارة حالة المحادثة عبر:

- حفظ المحادثة في Cache
- تتبع الفلاتر المجمعة
- تتبع الحقول الناقصة
- إدارة حالة انتظار التأكيد
- الحفاظ على سجل المحادثة

### جمع المعلومات التدريجي

النظام لا يسأل كل الأسئلة دفعة واحدة:

```
المستخدم: "أريد بيت"
المساعد: "📍 في أي محافظة أو مدينة تريد؟"

المستخدم: "الناصرية"
المساعد: "💰 ما هي ميزانيتك التقريبية؟"

المستخدم: "150 مليون"
المساعد: [يبحث ويعرض النتائج]
```

### إدارة التأكيدات

قبل تنفيذ الإجراءات المهمة، يطلب النظام التأكيد:

```
المساعد: حسناً، سأنشئ إعلان بيع عقار لك:
نوع العقار: بيت
الموقع: الناصرية
المساحة: 200 م²
السعر: 150 مليون

هل تريد المتابعة؟
[✅ نعم، متابعة] [✏️ تعديل] [❌ إلغاء]
```

---

## 🎨 Result Renderer

### بطاقات النتائج

يقوم `ResultRenderer` بتحويل نتائج البحث إلى بطاقات منسقة:

#### بطاقة العقار
```
🏠 بيت للبيع
📍 الناصرية
💰 150,000,000 د.ع
📐 200 م²
🛏️ 3 غرف
⭐ مطابقة: 85%

[👁️ عرض المنشور] [💬 مراسلة الدلال]
```

#### بطاقة الفندق
```
🏨 فندق بغداد
📍 بغداد
⭐ ⭐⭐⭐
💰 فاخر
⭐ مطابقة: 90%

[👁️ عرض الفندق]
```

#### بطاقة الوظيفة
```
💼 وظيفة محاسب
📍 الناصرية
🏢 شركة العراق
💰 من 1,000,000 د.ع
⭐ مطابقة: 75%

[👁️ عرض الوظيفة]
```

### الإجراءات المدعومة

- `view` - عرض المنشور
- `contact_broker` - مراسلة الدلال
- `contact` - التواصل العام

---

## 🔌 API Endpoints

### `/api/ai/smart/chat/`
**نوع:** POST  
**الصلاحية:** IsAuthenticated

**طلب:**
```json
{
  "message": "أريد بيت في الناصرية",
  "conversation_id": "conv-uuid",
  "render_results": true
}
```

**استجابة:**
```json
{
  "response": "وجدت 3 نتائج...",
  "action": "show_results",
  "results": [...],
  "rendered_results": [...],
  "metadata": {...},
  "conversation_id": "conv-uuid"
}
```

### `/api/ai/smart/reset/`
**نوع:** POST  
**الصلاحية:** IsAuthenticated

**طلب:**
```json
{
  "conversation_id": "conv-uuid"
}
```

**استجابة:**
```json
{
  "success": true,
  "message": "Conversation reset successfully",
  "conversation_id": "conv-uuid"
}
```

### `/api/ai/smart/state/`
**نوع:** GET  
**الصلاحية:** IsAuthenticated

**معاملات:**
- `conversation_id` - UUID المحادثة

**استجابة:**
```json
{
  "success": true,
  "state": {
    "conversation_id": "conv-uuid",
    "current_intent": "buy_property",
    "collected_filters": {...},
    "missing_fields": [...],
    "conversation_history": [...]
  }
}
```

### `/api/ai/smart/confirm/`
**نوع:** POST  
**الصلاحية:** IsAuthenticated

**طلب:**
```json
{
  "conversation_id": "conv-uuid",
  "confirmed": true
}
```

### `/api/ai/suggest-alternatives/`
**نوع:** POST  
**الصلاحية:** IsAuthenticated

**طلب:**
```json
{
  "conversation_id": "conv-uuid"
}
```

---

## 🎯 Frontend Integration

### واجهة المستخدم

الواجهة موجودة في:
- **Template:** `templates/properties/ai_smart_assistant.html`
- **CSS:** `static/css/ai_smart_assistant.css`
- **JS:** `static/js/ai_smart_assistant.js`

### الميزات

1. **واجهة دردشة حديثة** - تصميم عصري داكن
2. **أزرار سريعة** - إجراءات شائعة بضغطة واحدة
3. **بطاقات النتائج** - عرض منسق للنتائج
4. **مؤشر الكتابة** - يعرف المستخدم أن النظام يعمل
5. **التكيف التلقائي** - حقل نص يتكيف مع المحتوى
6. **تصميم متجاوب** - يعمل على جميع الأجهزة

### التفاعل

```javascript
// إرسال رسالة
assistant.sendMessage("أريد بيت في الناصرية");

// إعادة تعيين المحادثة
assistant.resetConversation();

// تأكيد إجراء
confirmAction('create_listing');

# طلب بدائل
suggestAlternatives();
```

---

## 🔒 الأمان

### المصادقة والترخيص

- جميع الـ endpoints تتطلب `IsAuthenticated`
- يعتمد على `request.user` للمصادقة
- لا يثق بـ user_id من input المستخدم

### الحماية من SQL Injection

- لا يسمح للـ LLM بإنشاء SQL خام
- جميع الاستعلامات تمر عبر Django ORM
- التحقق من صحة الفلاتر قبل الاستخدام

### الحماية من IDOR

- كل محادثة مرتبطة بـ user_id
- لا يمكن للمستخدم الوصول لمحادثات الآخرين
- التحقق من الصلاحيات لكل إجراء

### الحماية من Hallucination

- النظام لا يخترع نتائج
- البحث فقط في قاعدة البيانات الفعلية
- عند عدم وجود نتائج، يوضح ذلك صراحة

---

## 📊 الأداء

### التحسينات

- **Query Optimization** - استخدام `select_related` و `prefetch_related`
- **Result Limiting** - حد أقصى 10 نتائج لكل بحث
- **Caching** - تخزين حالة المحادثة في Cache
- **Lazy Loading** - تحميل الأنظمة الفرعية عند الحاجة فقط

### المراقبة

يتم تسجيل:
- الـ intent المكتشفة
- نوع البحث
- نجاح/فشل البحث
- المدة الزمنية
- الـ provider المستخدم

---

## 🧪 الاختبارات

### مجموعات الاختبارات

1. **IntentDetectionTests** - اختبارات اكتشاف النوايا
2. **RequestParserTests** - اختبارات محلل الطلبات
3. **SearchServiceTests** - اختبارات خدمة البحث
4. **ConversationManagerTests** - اختبارات مدير المحادثات
5. **ResultRendererTests** - اختبارات معالج النتائج
6. **APITests** - اختبارات الـ API
7. **SecurityTests** - اختبارات الأمان
8. **IraqiDialectTests** - اختبارات اللهجة العراقية
9. **IntegrationTests** - اختبارات التكامل

### تشغيل الاختبارات

```bash
# تشغيل جميع اختبارات المساعد الذكي
python manage.py test properties.tests_ai_smart_assistant

# تشغيل مجموعة اختبارات محددة
python manage.py test properties.tests_ai_smart_assistant.IntentDetectionTests

# تشغيل اختبار محدد
python manage.py test properties.tests_ai_smart_assistant.IntentDetectionTests.test_buy_property_intent_arabic
```

---

## 🚀 التطوير المستقبلي

### الميزات المقترحة

1. **Rate Limiting** - الحد من طلبات المستخدم
2. **Voice Input** - دعم الإدخال الصوتي
3. **Multi-language** - دعم لغات إضافية
4. **Advanced Filters** - فلاتر أكثر تعقيداً
5. **Saved Searches** - حفظ عمليات البحث
6. **Recommendations** - توصيات ذكية
7. **Analytics** - تحليلات الاستخدام
8. **A/B Testing** - اختبار تحسينات النظام

---

## 📞 الدعم والتواصل

للإبلاغ عن مشاكل أو اقتراح تحسينات:

1. راجع `AI_SMART_SEARCH_AUDIT.md` للمشاكل المعروفة
2. راجع `AI_SMART_SEARCH_TEST_REPORT.md` لنتائج الاختبارات
3. افتح issue في نظام تتبع المشاكل

---

## 📝 ملاحظات مهمة

- **لا ت删除 أي بيانات** - النظام محافظ للبيانات
- **لا يغير Models بدون migrations** - أي تغيير يتطلب migration
- **لا يكسر الميزات الموجودة** - متوافق مع الأنظمة الحالية
- **لا يخترق الأمان** - يتبع أفضل ممارسات Django الأمنية
- **لا يعتمد على LLM لـ SQL** - جميع الاستعلامات عبر ORM
- **لا يعرض secrets** - لا يكشف معلومات حساسة في logs

---

**النظام جاهز للاستخدام في بيئة Production مع المتطلبات الأساسية.** ✅
