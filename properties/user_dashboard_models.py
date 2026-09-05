# ==================== USER DASHBOARD MODELS ====================
# These models should be added to properties/models.py

class SavedProperty(models.Model):
    """العقارات المحفوظة من قبل المستخدمين"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_properties', verbose_name='المستخدم')
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='saved_by', verbose_name='العقار')
    saved_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الحفظ')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    
    class Meta:
        verbose_name = 'عقار محفوظ'
        verbose_name_plural = 'العقارات المحفوظة'
        unique_together = ['user', 'property']
        indexes = [
            models.Index(fields=['user', '-saved_at']),
            models.Index(fields=['property']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.property.title}"


class UserInterest(models.Model):
    """اهتمامات المستخدم المخصصة"""
    
    INTEREST_TYPES = [
        ('residential', 'سكني'),
        ('commercial', 'تجاري'),
        ('land', 'أرض'),
        ('apartment', 'شقة'),
        ('villa', 'فيلا'),
        ('hotel', 'فندق'),
        ('resort', 'منتجع'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interests', verbose_name='المستخدم')
    interest_type = models.CharField(max_length=20, choices=INTEREST_TYPES, verbose_name='نوع الاهتمام')
    level = models.IntegerField(default=50, verbose_name='مستوى الاهتمام (0-100)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')
    
    class Meta:
        verbose_name = 'اهتمام المستخدم'
        verbose_name_plural = 'اهتمامات المستخدم'
        unique_together = ['user', 'interest_type']
        indexes = [
            models.Index(fields=['user', 'interest_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_interest_type_display()}"


class FavoriteLocation(models.Model):
    """المناطق المفضلة للمستخدم"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_locations', verbose_name='المستخدم')
    governorate = models.CharField(max_length=50, choices=IRAQ_GOVERNORATES, verbose_name='المحافظة')
    city = models.CharField(max_length=100, verbose_name='المدينة')
    district = models.CharField(max_length=100, blank=True, verbose_name='القضاء')
    area = models.CharField(max_length=100, blank=True, verbose_name='المنطقة')
    priority = models.IntegerField(default=1, verbose_name='الأولوية')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإضافة')
    
    class Meta:
        verbose_name = 'منطقة مفضلة'
        verbose_name_plural = 'المناطق المفضلة'
        indexes = [
            models.Index(fields=['user', '-priority']),
            models.Index(fields=['governorate', 'city']),
        ]
    
    def __str__(self):
        location = f"{self.governorate} - {self.city}"
        if self.district:
            location += f" - {self.district}"
        if self.area:
            location += f" - {self.area}"
        return f"{self.user.username} - {location}"


class PriceAlert(models.Model):
    """تنبيهات الأسعار للمستخدمين"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='price_alerts', verbose_name='المستخدم')
    property_type = models.CharField(max_length=50, blank=True, verbose_name='نوع العقار')
    location = models.CharField(max_length=200, blank=True, verbose_name='الموقع')
    min_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='الحد الأدنى للسعر')
    max_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='الحد الأقصى للسعر')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    last_triggered = models.DateTimeField(null=True, blank=True, verbose_name='آخر تفعيل')
    
    class Meta:
        verbose_name = 'تنبيه سعر'
        verbose_name_plural = 'تنبيهات الأسعار'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.location or 'الكل'} - {self.min_price or 0} - {self.max_price or 'غير محدود'}"


class PropertyAlert(models.Model):
    """تنبيهات العقارات الجديدة"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_alerts', verbose_name='المستخدم')
    name = models.CharField(max_length=100, verbose_name='اسم التنبيه')
    filters = models.JSONField(verbose_name='الفلاتر')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    last_triggered = models.DateTimeField(null=True, blank=True, verbose_name='آخر تفعيل')
    
    class Meta:
        verbose_name = 'تنبيه عقارات'
        verbose_name_plural = 'تنبيهات العقارات'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"


class ViewingRequest(models.Model):
    """طلبات المعاينة"""
    
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('confirmed', 'مؤكد'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='viewing_requests', verbose_name='المستخدم')
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='viewing_requests', verbose_name='العقار')
    viewing_date = models.DateTimeField(verbose_name='تاريخ المعاينة')
    viewing_time = models.TimeField(verbose_name='وقت المعاينة')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الطلب')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')
    
    class Meta:
        verbose_name = 'طلب معاينة'
        verbose_name_plural = 'طلبات المعاينة'
        indexes = [
            models.Index(fields=['user', '-viewing_date']),
            models.Index(fields=['property']),
            models.Index(fields=['status', 'viewing_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.property.title} - {self.viewing_date}"


class HotelBooking(models.Model):
    """حجوزات الفنادق"""
    
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('confirmed', 'مؤكد'),
        ('checked_in', 'تم الدخول'),
        ('checked_out', 'تم الخروج'),
        ('cancelled', 'ملغي'),
        ('no_show', 'لم يحضر'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hotel_bookings', verbose_name='المستخدم')
    hotel = models.ForeignKey('Hotel', on_delete=models.CASCADE, related_name='bookings', verbose_name='الفندق')
    check_in = models.DateField(verbose_name='تاريخ الدخول')
    check_out = models.DateField(verbose_name='تاريخ الخروج')
    guests = models.IntegerField(default=1, verbose_name='عدد الضيوف')
    rooms = models.IntegerField(default=1, verbose_name='عدد الغرف')
    total_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='السعر الإجمالي')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    special_requests = models.TextField(blank=True, verbose_name='طلبات خاصة')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الحجز')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')
    
    class Meta:
        verbose_name = 'حجز فندق'
        verbose_name_plural = 'حجوزات الفنادق'
        indexes = [
            models.Index(fields=['user', '-check_in']),
            models.Index(fields=['hotel']),
            models.Index(fields=['status', 'check_in']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.hotel.name} - {self.check_in} إلى {self.check_out}"
