# ==================== HOTEL AND TRAVEL BOOKING MODELS ====================
# These models should be added to properties/models.py

class HotelBooking(models.Model):
    """حجوزات الفنادق"""
    
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('confirmed', 'مؤكد'),
        ('paid', 'مدفوع'),
        ('checked_in', 'تم الدخول'),
        ('checked_out', 'تم الخروج'),
        ('cancelled', 'ملغي'),
        ('no_show', 'لم يحضر'),
        ('refunded', 'مسترد'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('processing', 'قيد المعالجة'),
        ('completed', 'مكتمل'),
        ('failed', 'فشل'),
        ('refunded', 'مسترد'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hotel_bookings', verbose_name='المستخدم')
    hotel = models.ForeignKey('Hotel', on_delete=models.CASCADE, related_name='bookings', verbose_name='الفندق')
    booking_reference = models.CharField(max_length=20, unique=True, verbose_name='رقم الحجز')
    
    # Dates
    check_in = models.DateField(verbose_name='تاريخ الدخول')
    check_out = models.DateField(verbose_name='تاريخ الخروج')
    nights = models.IntegerField(verbose_name='عدد الليالي')
    
    # Room details
    room_type = models.CharField(max_length=50, verbose_name='نوع الغرفة')
    rooms_count = models.IntegerField(default=1, verbose_name='عدد الغرف')
    guests = models.IntegerField(default=1, verbose_name='عدد الضيوف')
    
    # Pricing
    base_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='السعر الأساسي')
    taxes = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='الضرائب')
    fees = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='الرسوم')
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='الخصم')
    total_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='السعر الإجمالي')
    
    # Payment
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name='حالة الدفع')
    payment_method = models.CharField(max_length=50, blank=True, verbose_name='طريقة الدفع')
    payment_id = models.CharField(max_length=100, blank=True, verbose_name='معرف الدفع')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    
    # Guest details
    guest_name = models.CharField(max_length=200, verbose_name='اسم الضيف')
    guest_email = models.EmailField(verbose_name='البريد الإلكتروني')
    guest_phone = models.CharField(max_length=20, verbose_name='رقم الهاتف')
    special_requests = models.TextField(blank=True, verbose_name='طلبات خاصة')
    
    # Cancellation
    cancellation_policy = models.TextField(blank=True, verbose_name='سياسة الإلغاء')
    is_cancellable = models.BooleanField(default=True, verbose_name='قابل للإلغاء')
    cancellation_deadline = models.DateTimeField(null=True, blank=True, verbose_name='موعد الإلغاء')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الحجز')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ التأكيد')
    
    class Meta:
        verbose_name = 'حجز فندق'
        verbose_name_plural = 'حجوزات الفنادق'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['hotel']),
            models.Index(fields=['status', 'check_in']),
            models.Index(fields=['booking_reference']),
            models.Index(fields=['payment_status']),
        ]
    
    def __str__(self):
        return f"{self.booking_reference} - {self.hotel.name}"
    
    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        if not self.nights:
            self.nights = (self.check_out - self.check_in).days
        super().save(*args, **kwargs)
    
    def generate_booking_reference(self):
        import random
        import string
        return 'HTL' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


class CarRental(models.Model):
    """تأجير السيارات"""
    
    CAR_TYPES = [
        ('economy', 'اقتصادية'),
        ('compact', 'صغيرة'),
        ('midsize', 'متوسطة'),
        ('fullsize', 'كبيرة'),
        ('luxury', 'فاخرة'),
        ('suv', 'دفع رباعي'),
        ('van', 'شاحنة صغيرة'),
        ('convertible', 'كوبيه'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('confirmed', 'مؤكد'),
        ('picked_up', 'تم الاستلام'),
        ('returned', 'تم الإرجاع'),
        ('cancelled', 'ملغي'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='car_rentals', verbose_name='المستخدم')
    rental_company = models.ForeignKey('ServiceProvider', on_delete=models.CASCADE, related_name='car_rentals', verbose_name='شركة التأجير')
    booking_reference = models.CharField(max_length=20, unique=True, verbose_name='رقم الحجز')
    
    # Rental details
    car_type = models.CharField(max_length=20, choices=CAR_TYPES, verbose_name='نوع السيارة')
    car_model = models.CharField(max_length=100, verbose_name='موديل السيارة')
    pickup_location = models.CharField(max_length=200, verbose_name='موقع الاستلام')
    dropoff_location = models.CharField(max_length=200, verbose_name='موقع الإرجاع')
    
    # Dates
    pickup_date = models.DateTimeField(verbose_name='تاريخ الاستلام')
    dropoff_date = models.DateTimeField(verbose_name='تاريخ الإرجاع')
    rental_days = models.IntegerField(verbose_name='عدد الأيام')
    
    # Pricing
    daily_rate = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='السعر اليومي')
    insurance = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='التأمين')
    fuel_charge = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='رسوم الوقود')
    total_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='السعر الإجمالي')
    
    # Driver details
    driver_name = models.CharField(max_length=200, verbose_name='اسم السائق')
    driver_license = models.CharField(max_length=50, verbose_name='رقم رخصة القيادة')
    driver_age = models.IntegerField(verbose_name='عمر السائق')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    
    # Special requests
    special_requests = models.TextField(blank=True, verbose_name='طلبات خاصة')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الحجز')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')
    
    class Meta:
        verbose_name = 'تأجير سيارة'
        verbose_name_plural = 'تأجير السيارات'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['rental_company']),
            models.Index(fields=['status', 'pickup_date']),
            models.Index(fields=['booking_reference']),
        ]
    
    def __str__(self):
        return f"{self.booking_reference} - {self.car_model}"
    
    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        if not self.rental_days:
            if self.pickup_date and self.dropoff_date:
                self.rental_days = (self.dropoff_date - self.pickup_date).days
        super().save(*args, **kwargs)
    
    def generate_booking_reference(self):
        import random
        import string
        return 'CAR' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


class TravelPackage(models.Model):
    """الرحلات السياحية"""
    
    PACKAGE_TYPES = [
        ('ready_made', 'برنامج جاهز'),
        ('custom', 'مخصص'),
        ('ai_generated', 'مولد بالذكاء الاصطناعي'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('published', 'منشور'),
        ('fully_booked', 'محجوز بالكامل'),
        ('cancelled', 'ملغي'),
        ('completed', 'مكتمل'),
    ]
    
    TRAVEL_TYPES = [
        ('domestic', 'داخلي'),
        ('international', 'دولي'),
        ('hajj', 'حج'),
        ('umrah', 'عمرة'),
        ('tourism', 'سياحة'),
        ('business', 'أعمال'),
        ('adventure', 'مغامرة'),
        ('medical', 'علاجي'),
        ('educational', 'تعليمي'),
        ('family', 'عائلي'),
        ('luxury', 'فاخر'),
        ('budget', 'اقتصادي'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_packages', verbose_name='المستخدم')
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPES, default='ready_made', verbose_name='نوع الرحلة')
    travel_type = models.CharField(max_length=20, choices=TRAVEL_TYPES, verbose_name='نوع السفر')
    
    # Package details
    title = models.CharField(max_length=200, verbose_name='عنوان الرحلة')
    description = models.TextField(verbose_name='وصف الرحلة')
    destination = models.CharField(max_length=200, verbose_name='الوجهة')
    country = models.ForeignKey('Country', on_delete=models.CASCADE, verbose_name='الدولة')
    
    # Dates
    start_date = models.DateField(verbose_name='تاريخ البداية')
    end_date = models.DateField(verbose_name='تاريخ النهاية')
    duration_days = models.IntegerField(verbose_name='مدة الرحلة (أيام)')
    
    # Pricing
    base_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='السعر الأساسي')
    flight_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='تكلفة الطيران')
    accommodation_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='تكلفة الإقامة')
    transportation_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='تكلفة النقل')
    activities_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='تكلفة الأنشطة')
    insurance_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='التأمين')
    total_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='السعر الإجمالي')
    
    # Capacity
    max_participants = models.IntegerField(verbose_name='الحد الأقصى للمشاركين')
    current_participants = models.IntegerField(default=0, verbose_name='المشاركين الحاليين')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='الحالة')
    is_featured = models.BooleanField(default=False, verbose_name='مميز')
    
    # AI generated
    ai_generated = models.BooleanField(default=False, verbose_name='مولد بالذكاء الاصطناعي')
    ai_confidence = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, verbose_name='ثقة الذكاء الاصطناعي')
    
    # Inclusions
    includes_flights = models.BooleanField(default=False, verbose_name='يشمل الطيران')
    includes_hotel = models.BooleanField(default=False, verbose_name='يشمل الفندق')
    includes_transport = models.BooleanField(default=False, verbose_name='يشمل النقل')
    includes_meals = models.BooleanField(default=False, verbose_name='يشمل الوجبات')
    includes_activities = models.BooleanField(default=False, verbose_name='يشمل الأنشطة')
    includes_insurance = models.BooleanField(default=False, verbose_name='يشمل التأمين')
    includes_guide = models.BooleanField(default=False, verbose_name='يشمل المرشد')
    
    # Images
    main_image = models.ImageField(upload_to='travel_packages/', blank=True, verbose_name='الصورة الرئيسية')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')
    
    class Meta:
        verbose_name = 'رحلة سياحية'
        verbose_name_plural = 'الرحلات السياحية'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['destination']),
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['travel_type']),
            models.Index(fields=['package_type']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.destination}"
    
    def save(self, *args, **kwargs):
        if not self.duration_days and self.start_date and self.end_date:
            self.duration_days = (self.end_date - self.start_date).days
        super().save(*args, **kwargs)


class TravelItinerary(models.Model):
    """الجدول الزمني للرحلة"""
    
    package = models.ForeignKey(TravelPackage, on_delete=models.CASCADE, related_name='itineraries', verbose_name='الرحلة')
    day_number = models.IntegerField(verbose_name='رقم اليوم')
    date = models.DateField(verbose_name='التاريخ')
    
    # Day activities
    title = models.CharField(max_length=200, verbose_name='عنوان اليوم')
    description = models.TextField(verbose_name='وصف اليوم')
    
    # Time slots
    morning_activity = models.TextField(blank=True, verbose_name='نشاط الصباح')
    afternoon_activity = models.TextField(blank=True, verbose_name='نشاط الظهيرة')
    evening_activity = models.TextField(blank=True, verbose_name='نشاط المساء')
    
    # Meals
    breakfast_included = models.BooleanField(default=False, verbose_name='الإفطار مشمول')
    lunch_included = models.BooleanField(default=False, verbose_name='الغداء مشمول')
    dinner_included = models.BooleanField(default=False, verbose_name='العشاء مشمول')
    
    # Accommodation
    accommodation = models.CharField(max_length=200, blank=True, verbose_name='الإقامة')
    accommodation_type = models.CharField(max_length=50, blank=True, verbose_name='نوع الإقامة')
    
    # Transportation
    transportation = models.CharField(max_length=200, blank=True, verbose_name='النقل')
    transportation_type = models.CharField(max_length=50, blank=True, verbose_name='نوع النقل')
    
    # Activities
    activities = models.JSONField(default=list, blank=True, verbose_name='الأنشطة')
    
    # Notes
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    
    # AI generated
    ai_generated = models.BooleanField(default=False, verbose_name='مولد بالذكاء الاصطناعي')
    
    class Meta:
        verbose_name = 'جدول زمني'
        verbose_name_plural = 'الجداول الزمنية'
        ordering = ['package', 'day_number']
        indexes = [
            models.Index(fields=['package', 'day_number']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.package.title} - اليوم {self.day_number}"


class TourGuide(models.Model):
    """المرشدين السياحيين"""
    
    LANGUAGES = [
        ('arabic', 'العربية'),
        ('english', 'الإنجليزية'),
        ('french', 'الفرنسية'),
        ('german', 'الألمانية'),
        ('spanish', 'الإسبانية'),
        ('italian', 'الإيطالية'),
        ('russian', 'الروسية'),
        ('chinese', 'الصينية'),
        ('japanese', 'اليابانية'),
        ('korean', 'الكورية'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guide_profile', verbose_name='المستخدم')
    
    # Personal info
    full_name = models.CharField(max_length=200, verbose_name='الاسم الكامل')
    languages = models.JSONField(verbose_name='اللغات')  # List of language codes
    languages_display = models.CharField(max_length=200, blank=True, verbose_name='اللغات (للعرض)')
    
    # Professional info
    experience_years = models.IntegerField(verbose_name='سنوات الخبرة')
    specializations = models.JSONField(default=list, blank=True, verbose_name='التخصصات')
    certifications = models.JSONField(default=list, blank=True, verbose_name='الشهادات')
    
    # Rating
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, verbose_name='التقييم')
    total_reviews = models.IntegerField(default=0, verbose_name='إجمالي التقييمات')
    
    # Availability
    is_available = models.BooleanField(default=True, verbose_name='متاح')
    available_destinations = models.JSONField(default=list, blank=True, verbose_name='الوجهات المتاحة')
    
    # Pricing
    daily_rate = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='السعر اليومي')
    hourly_rate = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='السعر بالساعة')
    
    # Contact
    phone = models.CharField(max_length=20, verbose_name='رقم الهاتف')
    email = models.EmailField(verbose_name='البريد الإلكتروني')
    
    # Profile
    bio = models.TextField(verbose_name='السيرة الذاتية')
    profile_image = models.ImageField(upload_to='guides/', blank=True, verbose_name='صورة الملف الشخصي')
    
    # Status
    is_verified = models.BooleanField(default=False, verbose_name='موثق')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')
    
    class Meta:
        verbose_name = 'مرشد سياحي'
        verbose_name_plural = 'المرشدون السياحيون'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_available', 'is_active']),
            models.Index(fields=['rating']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return f"{self.full_name} - {self.rating} ⭐"


class HotelRating(models.Model):
    """تقييمات الفنادق الموثقة"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hotel_ratings', verbose_name='المستخدم')
    hotel = models.ForeignKey('Hotel', on_delete=models.CASCADE, related_name='ratings', verbose_name='الفندق')
    booking = models.ForeignKey(HotelBooking, on_delete=models.CASCADE, related_name='rating', verbose_name='الحجز')
    
    # Rating criteria
    cleanliness = models.IntegerField(verbose_name='النظافة (1-5)')
    location = models.IntegerField(verbose_name='الموقع (1-5)')
    service = models.IntegerField(verbose_name='الخدمة (1-5)')
    value = models.IntegerField(verbose_name='القيمة (1-5)')
    facilities = models.IntegerField(verbose_name='المرافق (1-5)')
    
    # Overall rating
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2, verbose_name='التقييم العام')
    
    # Review
    title = models.CharField(max_length=200, verbose_name='عنوان التقييم')
    review = models.TextField(verbose_name='التقييم')
    
    # Verification
    is_verified_booking = models.BooleanField(default=True, verbose_name='حجز موثق')
    verified_stay_date = models.DateField(verbose_name='تاريخ الإقامة الموثق')
    
    # Images
    images = models.JSONField(default=list, blank=True, verbose_name='الصور')
    
    # Status
    is_approved = models.BooleanField(default=False, verbose_name='موافق عليه')
    is_featured = models.BooleanField(default=False, verbose_name='مميز')
    
    # Response from hotel
    hotel_response = models.TextField(blank=True, verbose_name='رد الفندق')
    hotel_response_date = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الرد')
    
    # Helpful votes
    helpful_count = models.IntegerField(default=0, verbose_name='عدد الأصوات المفيدة')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التقييم')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')
    
    class Meta:
        verbose_name = 'تقييم فندق'
        verbose_name_plural = 'تقييمات الفنادق'
        unique_together = ['user', 'booking']
        indexes = [
            models.Index(fields=['hotel', '-created_at']),
            models.Index(fields=['overall_rating']),
            models.Index(fields=['is_verified_booking']),
            models.Index(fields=['is_approved']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.hotel.name} - {self.overall_rating} ⭐"
    
    def save(self, *args, **kwargs):
        # Calculate overall rating
        total = self.cleanliness + self.location + self.service + self.value + self.facilities
        self.overall_rating = total / 5
        super().save(*args, **kwargs)


class HotelPointsSystem(models.Model):
    """نظام نقاط الفنادق"""
    
    hotel = models.OneToOneField('Hotel', on_delete=models.CASCADE, related_name='points_system', verbose_name='الفندق')
    
    # Points
    total_points = models.IntegerField(default=0, verbose_name='إجمالي النقاط')
    available_points = models.IntegerField(default=0, verbose_name='النقاط المتاحة')
    redeemed_points = models.IntegerField(default=0, verbose_name='النقاط المستبدلة')
    
    # Level
    level = models.IntegerField(default=1, verbose_name='المستوى')
    level_name = models.CharField(max_length=50, blank=True, verbose_name='اسم المستوى')
    
    # Benefits
    benefits = models.JSONField(default=list, blank=True, verbose_name='المزايا')
    
    # Points history
    points_history = models.JSONField(default=list, blank=True, verbose_name='سجل النقاط')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')
    
    class Meta:
        verbose_name = 'نظام نقاط الفندق'
        verbose_name_plural = 'أنظمة نقاط الفنادق'
        indexes = [
            models.Index(fields=['total_points']),
            models.Index(fields=['level']),
        ]
    
    def __str__(self):
        return f"{self.hotel.name} - {self.total_points} نقطة - المستوى {self.level}"
    
    def add_points(self, points, reason):
        """إضافة نقاط"""
        self.total_points += points
        self.available_points += points
        self.points_history.append({
            'action': 'add',
            'points': points,
            'reason': reason,
            'date': timezone.now().isoformat()
        })
        self.update_level()
        self.save()
    
    def redeem_points(self, points, reason):
        """استبدال نقاط"""
        if self.available_points >= points:
            self.available_points -= points
            self.redeemed_points += points
            self.points_history.append({
                'action': 'redeem',
                'points': points,
                'reason': reason,
                'date': timezone.now().isoformat()
            })
            self.save()
            return True
        return False
    
    def update_level(self):
        """تحديث المستوى بناءً على النقاط"""
        if self.total_points >= 10000:
            self.level = 5
            self.level_name = 'ذهبي'
        elif self.total_points >= 5000:
            self.level = 4
            self.level_name = 'بلاتيني'
        elif self.total_points >= 2000:
            self.level = 3
            self.level_name = 'فضي'
        elif self.total_points >= 500:
            self.level = 2
            self.level_name = 'برونزي'
        else:
            self.level = 1
            self.level_name = 'عضو'
        
        self.update_benefits()
    
    def update_benefits(self):
        """تحديث المزايا بناءً على المستوى"""
        benefits_map = {
            1: ['حجز مجاني', 'دعم على مدار الساعة'],
            2: ['خصم 5%', 'إمكانية إلغاء متأخر', 'وجبة مجانية'],
            3: ['خصم 10%', 'غرفة مجانية', 'إمكانية الدخول المبكر'],
            4: ['خصم 15%', 'ترقية غرفة مجانية', 'خدمة كونسييرج'],
            5: ['خصم 20%', 'جناح فاخر مجاني', 'خدمة خاصة', 'حفلة ترحيبية']
        }
        self.benefits = benefits_map.get(self.level, [])


class HotelPriceAlert(models.Model):
    """تنبيهات انخفاض أسعار الفنادق"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hotel_price_alerts', verbose_name='المستخدم')
    hotel = models.ForeignKey('Hotel', on_delete=models.CASCADE, related_name='price_alerts', verbose_name='الفندق')
    
    # Alert criteria
    target_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='السعر المستهدف')
    current_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='السعر الحالي')
    price_drop_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='نسبة الانخفاض')
    
    # Date range
    check_in_date = models.DateField(verbose_name='تاريخ الدخول')
    check_out_date = models.DateField(verbose_name='تاريخ الخروج')
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    is_triggered = models.BooleanField(default=False, verbose_name='تم التفعيل')
    
    # Notification
    notification_sent = models.BooleanField(default=False, verbose_name='تم إرسال الإشعار')
    notification_date = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الإشعار')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')
    
    class Meta:
        verbose_name = 'تنبيه سعر فندق'
        verbose_name_plural = 'تنبيهات أسعار الفنادق'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['hotel']),
            models.Index(fields=['is_active', 'is_triggered']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.hotel.name} - {self.target_price}"
    
    def check_price_drop(self):
        """التحقق من انخفاض السعر"""
        if self.current_price <= self.target_price:
            self.is_triggered = True
            self.price_drop_percentage = ((self.current_price - self.target_price) / self.target_price) * 100
            self.save()
            return True
        return False


class TravelBooking(models.Model):
    """حجز الرحلات الشاملة"""
    
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('confirmed', 'مؤكد'),
        ('paid', 'مدفوع'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_bookings', verbose_name='المستخدم')
    package = models.ForeignKey(TravelPackage, on_delete=models.CASCADE, related_name='bookings', verbose_name='الرحلة')
    booking_reference = models.CharField(max_length=20, unique=True, verbose_name='رقم الحجز')
    
    # Participants
    adults_count = models.IntegerField(default=1, verbose_name='عدد البالغين')
    children_count = models.IntegerField(default=0, verbose_name='عدد الأطفال')
    infants_count = models.IntegerField(default=0, verbose_name='عدد الرضع')
    
    # Dates
    departure_date = models.DateField(verbose_name='تاريخ المغادرة')
    return_date = models.DateField(verbose_name='تاريخ العودة')
    
    # Pricing
    base_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='السعر الأساسي')
    additional_charges = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='رسوم إضافية')
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='الخصم')
    total_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='السعر الإجمالي')
    
    # Payment
    payment_status = models.CharField(max_length=20, choices=HotelBooking.PAYMENT_STATUS_CHOICES, default='pending', verbose_name='حالة الدفع')
    payment_method = models.CharField(max_length=50, blank=True, verbose_name='طريقة الدفع')
    payment_id = models.CharField(max_length=100, blank=True, verbose_name='معرف الدفع')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    
    # Guest details
    lead_guest_name = models.CharField(max_length=200, verbose_name='اسم الضيف الرئيسي')
    lead_guest_email = models.EmailField(verbose_name='البريد الإلكتروني')
    lead_guest_phone = models.CharField(max_length=20, verbose_name='رقم الهاتف')
    
    # Special requests
    special_requests = models.TextField(blank=True, verbose_name='طلبات خاصة')
    
    # Inclusions
    includes_flight = models.BooleanField(default=False, verbose_name='يشمل الطيران')
    includes_hotel = models.BooleanField(default=False, verbose_name='يشمل الفندق')
    includes_car = models.BooleanField(default=False, verbose_name='يشمل السيارة')
    includes_guide = models.BooleanField(default=False, verbose_name='يشمل المرشد')
    
    # Guide assignment
    assigned_guide = models.ForeignKey(TourGuide, on_delete=models.SET_NULL, null=True, blank=True, related_name='guided_bookings', verbose_name='المرشد المسند')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الحجز')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ التأكيد')
    
    class Meta:
        verbose_name = 'حجز رحلة'
        verbose_name_plural = 'حجوزات الرحلات'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['package']),
            models.Index(fields=['status', 'departure_date']),
            models.Index(fields=['booking_reference']),
        ]
    
    def __str__(self):
        return f"{self.booking_reference} - {self.package.title}"
    
    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        super().save(*args, **kwargs)
    
    def generate_booking_reference(self):
        import random
        import string
        return 'TRV' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))