# إعداد Google OAuth للمنصة

## المشكلة الحالية
Google Login غير متاح لأن مفاتيح OAuth غير معينة في متغيرات البيئة.

## حل سريع: تفعيل Google Login

### الخطوة 1: إنشاء مشروع Google Cloud (5 دقائق)

1. اذهب إلى [Google Cloud Console](https://console.cloud.google.com/)
2. سجل الدخول بحساب Google
3. انقر على **Select a project** > **NEW PROJECT**
4. اسم المشروع: `Dalal Platform`
5. انقر **CREATE**

### الخطوة 2: تفعيل Google+ API (2 دقيقة)

1. من القائمة، اختر **APIs & Services** > **Library**
2. ابحث عن `Google+ API API`
3. انقر عليه ثم **ENABLE**

### الخطوة 3: تكوين شاشة الموافقة (3 دقائق)

1. من القائمة، اختر **APIs & Services** > **OAuth consent screen**
2. اختر **External** ثم **CREATE**
3. أدخل المعلومات:
   - **App name**: دلال
   - **User support email**: بريدك الإلكتروني
   - **Developer contact**: بريدك الإلكتروني
4. انقر **SAVE AND CONTINUE** حتى النهاية
5. انقر **BACK TO DASHBOARD**

### الخطوة 4: إنشاء بيانات الاعتماد (3 دقائق)

1. من القائمة، اختر **APIs & Services** > **Credentials**
2. انقر **CREATE CREDENTIALS** > **OAuth client ID**
3. اختر **Web application**
4. **Name**: Dalal Web App
5. **Authorized redirect URIs** (أضف جميع هذه):
   ```
   https://muqq.up.railway.app/social/complete/google-oauth2/
   https://ff-production-38a4.up.railway.app/social/complete/google-oauth2/
   https://mup.up.railway.app/social/complete/google-oauth2/
   https://muq.up.railway.app/social/complete/google-oauth2/
   https://daluailiraq.com/social/complete/google-oauth2/
   https://www.daluailiraq.com/social/complete/google-oauth2/
   http://localhost:8000/social/complete/google-oauth2/
   http://127.0.0.1:8000/social/complete/google-oauth2/
   ```
6. انقر **CREATE**

### الخطوة 5: نسخ المفاتيح

بعد الإنشاء، ستحصل على:
- **Client ID**: انسخه (مثل: `123456789-abc123.apps.googleusercontent.com`)
- **Client Secret**: انسخه (مثل: `GOCSPX-abc123`)

### الخطوة 6: إضافة المفاتيح إلى Railway (2 دقيقة)

1. اذهب إلى [Railway](https://railway.app/)
2. اختر مشروعك
3. انتقل إلى **Variables**
4. أضف متغيرين جديدين:

   **المتغير الأول:**
   - Name: `SOCIAL_AUTH_GOOGLE_OAUTH2_KEY`
   - Value: `your-client-id-here` (استبدل بالـ Client ID الحقيقي)

   **المتغير الثاني:**
   - Name: `SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET`
   - Value: `your-client-secret-here` (استبدل بالـ Client Secret الحقيقي)

5. انقر **Deploy** لإعادة النشر

## الحل: إعداد Google OAuth

### الخطوة 1: إنشاء مشروع في Google Cloud Console

1. اذهب إلى [Google Cloud Console](https://console.cloud.google.com/)
2. سجل الدخول بحساب Google الخاص بك
3. أنشئ مشروع جديد أو اختر مشروع موجود
4. فعّل Google+ API أو Google Identity Platform

### الخطوة 2: إنشاء بيانات اعتماد OAuth 2.0

1. من القائمة الجانبية، اختر **APIs & Services** > **Credentials**
2. انقر على **Create Credentials** > **OAuth client ID**
3. إذا طُلب منك، قم بتهيئة شاشة الموافقة (OAuth consent screen):
   - اختر **External** (للمستخدمين العامين)
   - أدخل معلومات التطبيق:
     - App name: دلال
     - User support email: بريدك الإلكتروني
     - Developer contact: بريدك الإلكتروني
4. بعد ذلك، اختر نوع التطبيق:
   - اختر **Web application**
5. أدخل التفاصيل التالية:
   - **Name**: Dalal Platform
   - **Authorized redirect URIs** (هام جداً):
     ```
     https://muqq.up.railway.app/social/complete/google-oauth2/
     https://ff-production-38a4.up.railway.app/social/complete/google-oauth2/
     https://mup.up.railway.app/social/complete/google-oauth2/
     https://muq.up.railway.app/social/complete/google-oauth2/
     https://daluailiraq.com/social/complete/google-oauth2/
     https://www.daluailiraq.com/social/complete/google-oauth2/
     ```
6. انقر على **Create**

### الخطوة 3: نسخ المفاتيح

بعد إنشاء بيانات الاعتماد، ستحصل على:
- **Client ID**: شكل يشبه `123456789-abc123def456.apps.googleusercontent.com`
- **Client Secret**: شكل يشبه `GOCSPX-abc123def456`

### الخطوة 4: إضافة المفاتيح إلى Railway

1. اذهب إلى مشروعك في [Railway](https://railway.app/)
2. اختر مشروع Django الخاص بك
3. انتقل إلى **Variables** tab
4. أضف المتغيرات التالية:

   ```
   SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your-client-id-here
   SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your-client-secret-here
   ```

5. استبدل `your-client-id-here` و `your-client-secret-here` بالمفاتيح الفعلية التي نسختها
6. انقر على **Deploy** لإعادة نشر التطبيق

### الخطوة 5: التحقق من الإعداد

بعد إعادة النشر:
1. اذهب إلى صفحة تسجيل الدخول
2. زر Google Login يجب أن يكون نشطاً الآن
3. يمكنك أيضاً زيارة `/social/diagnostics/` للتحقق من حالة الإعداد

## ملاحظات مهمة

1. **Redirect URI**: تأكد من إضافة جميع النطاقات المحتملة
2. **Production**: في بيئة الإنتاج، تأكد من استخدام HTTPS
3. **Domain Verification**: قد تحتاج إلى التحقق من النطاق في Google Console
4. **Security**: لا تشارك المفاتيح مع أي شخص ولا تضعها في الكود المصدري

## استكشاف الأخطاء

### زر Google Login لا يزال معطلاً
- تأكد من إضافة المتغيرات في Railway بشكل صحيح
- تحقق من إعادة نشر التطبيق
- تأكد من أن Client ID و Client Secret صحيحان

### خطأ "redirect_uri_mismatch"
- تحقق من أن Redirect URI في Google Console يطابق تماماً ما في الكود
- تأكد من إضافة الشرطة المائلة النهائية `/`

### خطأ "invalid_client"
- تأكد من أن Client ID صحيح
- تحقق من أن المشروع في Google Cloud Console نشط

## الدعم

إذا واجهت أي مشاكل، راجع:
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Python Social Auth Documentation](https://python-social-auth.readthedocs.io/)

## تشخيص المشاكل

### كيفية التحقق من الإعداد:

1. **فحص متغيرات البيئة:**
   ```bash
   # في Railway، انتقل إلى Variables tab وتحقق من وجود:
   # - SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
   # - SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET
   ```

2. **فحص حالة المصادقة:**
   - اذهب إلى `/social/diagnostics/` في المتصفح
   - هذا سيعرض حالة جميع مزودي المصادقة

3. **فحص سجلات الأخطاء:**
   - في Railway، انتقل إلى Logs tab
   - ابحث عن أخطاء تتعلق بـ Google OAuth

### الحلول الشائعة:

1. **زر Google Login لا يظهر:**
   - تأكد من إضافة المتغيرات في Railway
   - تأكد من إعادة نشر التطبيق
   - تحقق من أن `GOOGLE_AUTH_AVAILABLE = True` في settings

2. **خطأ redirect_uri_mismatch:**
   - تأكد من إضافة جميع النطاقات في Google Console
   - تأكد من وجود الشرطة المائلة النهائية `/`

3. **خطأ invalid_client:**
   - تأكد من صحة Client ID
   - تأكد من أن المشروع نشط في Google Console
