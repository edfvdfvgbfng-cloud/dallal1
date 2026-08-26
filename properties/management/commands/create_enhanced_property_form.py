"""
Django Management Command to Create Enhanced Property Form Template
أمر إدارة Django لإنشاء قالب نموذج عقار محسّن
"""

import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Create enhanced property form template with all new fields'

    def handle(self, *args, **options):
        # Create the enhanced form template
        template_content = '''{% extends 'properties/base.html' %}
{% load static %}

{% block title %}إضافة عقار{% endblock %}

{% block content %}
<div class="enhanced-property-form-container">
    <div class="container">
        <div class="row">
            <div class="col-lg-12">
                <div class="form-card">
                    <div class="form-header">
                        <h1 class="form-title">إضافة عقار جديد</h1>
                        <p class="form-subtitle">أكمل جميع المعلومات المطلوبة للإعلان عن عقارك</p>
                        
                        <div class="progress-indicator">
                            <div class="progress-step active" data-step="1">
                                <span class="step-number">1</span>
                                <span class="step-label">المعلومات الأساسية</span>
                            </div>
                            <div class="progress-step" data-step="2">
                                <span class="step-number">2</span>
                                <span class="step-label">الموقع والمساحة</span>
                            </div>
                            <div class="progress-step" data-step="3">
                                <span class="step-number">3</span>
                                <span class="step-label">التفاصيل والمميزات</span>
                            </div>
                            <div class="progress-step" data-step="4">
                                <span class="step-number">4</span>
                                <span class="step-label">المستندات والقانونية</span>
                            </div>
                            <div class="progress-step" data-step="5">
                                <span class="step-number">5</span>
                                <span class="step-label">التسعير والنشر</span>
                            </div>
                        </div>
                    </div>

                    <form method="post" enctype="multipart/form-data" class="enhanced-property-form" id="propertyForm">
                        {% csrf_token %}
                        
                        {% if form.errors %}
                        <div class="alert alert-danger">
                            <div class="alert-icon">
                                <i class="fas fa-exclamation-triangle"></i>
                            </div>
                            <div class="alert-content">
                                <h4>يرجى تصحيح الأخطاء التالية:</h4>
                                <ul>
                                    {% for field, errors in form.errors.items %}
                                        {% for error in errors %}
                                            <li>{{ field }}: {{ error }}</li>
                                        {% endfor %}
                                    {% endfor %}
                                </ul>
                            </div>
                        </div>
                        {% endif %}
                        
                        <!-- Step 1: Basic Information -->
                        <div class="form-section active" data-section="1">
                            <h3 class="section-title">
                                <i class="fas fa-info-circle section-icon"></i>
                                المعلومات الأساسية
                            </h3>
                            
                            <div class="form-grid">
                                <div class="form-group full-width">
                                    <label for="{{ form.title.id_for_label }}" class="form-label">عنوان الإعلان <span class="required">*</span></label>
                                    {{ form.title }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.category.id_for_label }}" class="form-label">التصنيف <span class="required">*</span></label>
                                    {{ form.category }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.type.id_for_label }}" class="form-label">نوع العقار <span class="required">*</span></label>
                                    {{ form.type }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.purpose.id_for_label }}" class="form-label">الغرض</label>
                                    {{ form.purpose }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.property_condition.id_for_label }}" class="form-label">حالة العقار</label>
                                    {{ form.property_condition }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.ownership_status.id_for_label }}" class="form-label">حالة الملكية</label>
                                    {{ form.ownership_status }}
                                </div>
                                
                                <div class="form-group full-width">
                                    <label for="{{ form.description.id_for_label }}" class="form-label">وصف العقار <span class="required">*</span></label>
                                    {{ form.description }}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Step 2: Location and Area -->
                        <div class="form-section" data-section="2">
                            <h3 class="section-title">
                                <i class="fas fa-map-marker-alt section-icon"></i>
                                الموقع والمساحة
                            </h3>
                            
                            <div class="form-grid">
                                <div class="form-group">
                                    <label for="{{ form.governorate.id_for_label }}" class="form-label">المحافظة <span class="required">*</span></label>
                                    {{ form.governorate }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.city.id_for_label }}" class="form-label">المدينة <span class="required">*</span></label>
                                    {{ form.city }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.district.id_for_label }}" class="form-label">الحي <span class="required">*</span></label>
                                    {{ form.district }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.subdistrict.id_for_label }}" class="form-label">القضاء</label>
                                    {{ form.subdistrict }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.street.id_for_label }}" class="form-label">الشارع</label>
                                    {{ form.street }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.landmark.id_for_label }}" class="form-label">أقرب نقطة دالة</label>
                                    {{ form.landmark }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.total_area.id_for_label }}" class="form-label">المساحة الكلية (م²) <span class="required">*</span></label>
                                    {{ form.total_area }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.building_area.id_for_label }}" class="form-label">مساحة البناء (م²)</label>
                                    {{ form.building_area }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.price.id_for_label }}" class="form-label">السعر (د.ع) <span class="required">*</span></label>
                                    {{ form.price }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.currency.id_for_label }}" class="form-label">العملة</label>
                                    {{ form.currency }}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Step 3: Details and Features -->
                        <div class="form-section" data-section="3">
                            <h3 class="section-title">
                                <i class="fas fa-building section-icon"></i>
                                التفاصيل والمميزات
                            </h3>
                            
                            <div class="form-grid">
                                <!-- Building Details -->
                                <div class="form-group">
                                    <label for="{{ form.year_built.id_for_label }}" class="form-label">سنة البناء</label>
                                    {{ form.year_built }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.total_floors.id_for_label }}" class="form-label">عدد الطوابق</label>
                                    {{ form.total_floors }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.floor_number.id_for_label }}" class="form-label">رقم الطابق</label>
                                    {{ form.floor_number }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.bedrooms.id_for_label }}" class="form-label">عدد الغرف</label>
                                    {{ form.bedrooms }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.living_rooms.id_for_label }}" class="form-label">عدد الصالات</label>
                                    {{ form.living_rooms }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.bathrooms.id_for_label }}" class="form-label">عدد الحمامات</label>
                                    {{ form.bathrooms }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.kitchens.id_for_label }}" class="form-label">عدد المطابخ</label>
                                    {{ form.kitchens }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.parking_spaces.id_for_label }}" class="form-label">مواقف السيارات</label>
                                    {{ form.parking_spaces }}
                                </div>
                                
                                <!-- Amenities -->
                                <div class="form-group full-width">
                                    <label class="form-label">المميزات الأساسية</label>
                                    <div class="checkbox-group">
                                        <label>{{ form.furnished }} مفروش</label>
                                        <label>{{ form.has_elevator }} مصعد</label>
                                        <label>{{ form.has_generator }} مولد</label>
                                        <label>{{ form.has_air_conditioning }} مكيف</label>
                                        <label>{{ form.has_internet }} إنترنت</label>
                                        <label>{{ form.has_security_system }} نظام أمان</label>
                                    </div>
                                </div>
                                
                                <!-- Additional Features -->
                                <div class="form-group full-width">
                                    <label class="form-label">مميزات إضافية</label>
                                    <div class="checkbox-group">
                                        <label>{{ form.has_pool }} مسبح</label>
                                        <label>{{ form.has_garden }} حديقة</label>
                                        <label>{{ form.has_maid_room }} غرفة خادمة</label>
                                        <label>{{ form.has_driver_room }} غرفة سائق</label>
                                        <label>{{ form.has_storage }} مخزن</label>
                                        <label>{{ form.has_garage }} كراج</label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Step 4: Documents and Legal -->
                        <div class="form-section" data-section="4">
                            <h3 class="section-title">
                                <i class="fas fa-file-alt section-icon"></i>
                                المستندات والقانونية
                            </h3>
                            
                            <div class="form-grid">
                                <div class="form-group">
                                    <label for="{{ form.deed_number.id_for_label }}" class="form-label">رقم الطابو</label>
                                    {{ form.deed_number }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.deed_date.id_for_label }}" class="form-label">تاريخ الطابو</label>
                                    {{ form.deed_date }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.deed_type.id_for_label }}" class="form-label">نوع الوثيقة</label>
                                    {{ form.deed_type }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.building_permit_number.id_for_label }}" class="form-label">رقم رخصة البناء</label>
                                    {{ form.building_permit_number }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.zoning_type.id_for_label }}" class="form-label">نوع المنطقة</label>
                                    {{ form.zoning_type }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.legal_status.id_for_label }}" class="form-label">الحالة القانونية</label>
                                    {{ form.legal_status }}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Step 5: Pricing and Publishing -->
                        <div class="form-section" data-section="5">
                            <h3 class="section-title">
                                <i class="fas fa-dollar-sign section-icon"></i>
                                التسعير والنشر
                            </h3>
                            
                            <div class="form-grid">
                                <div class="form-group">
                                    <label for="{{ form.negotiable.id_for_label }}" class="form-label">قابل للتفاوض</label>
                                    {{ form.negotiable }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.down_payment.id_for_label }}" class="form-label">الدفعة الأولى</label>
                                    {{ form.down_payment }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.installments.id_for_label }}" class="form-label">الأقساط</label>
                                    {{ form.installments }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.publication_type.id_for_label }}" class="form-label">نوع النشر</label>
                                    {{ form.publication_type }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.publication_days.id_for_label }}" class="form-label">مدة النشر (أيام)</label>
                                    {{ form.publication_days }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.is_featured.id_for_label }}" class="form-label">عقار مميز</label>
                                    {{ form.is_featured }}
                                </div>
                                
                                <div class="form-group">
                                    <label for="{{ form.is_urgent.id_for_label }}" class="form-label">عاجل</label>
                                    {{ form.is_urgent }}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Navigation Buttons -->
                        <div class="form-navigation">
                            <button type="button" class="btn btn-secondary prev-btn" id="prevBtn" style="display: none;">
                                <i class="fas fa-arrow-right me-2"></i>السابق
                            </button>
                            <button type="button" class="btn btn-primary next-btn" id="nextBtn">
                                التالي<i class="fas fa-arrow-left ms-2"></i>
                            </button>
                            <button type="submit" class="btn btn-success submit-btn" id="submitBtn" style="display: none;">
                                <i class="fas fa-check me-2"></i>نشر العقار
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_css %}
<style>
.enhanced-property-form-container {
    padding: 40px 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

.form-card {
    background-color: white;
    border-radius: 20px;
    padding: 40px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.form-header {
    text-align: center;
    margin-bottom: 40px;
    padding-bottom: 30px;
    border-bottom: 2px solid #f0f0f0;
}

.form-title {
    font-size: 32px;
    font-weight: bold;
    color: #333;
    margin-bottom: 10px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.form-subtitle {
    font-size: 16px;
    color: #666;
    margin: 0;
}

.progress-indicator {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 30px;
}

.progress-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    opacity: 0.5;
    transition: all 0.3s;
}

.progress-step.active {
    opacity: 1;
}

.step-number {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: #e0e0e0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    color: #666;
    transition: all 0.3s;
}

.progress-step.active .step-number {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.step-label {
    font-size: 12px;
    color: #666;
    font-weight: 500;
}

.form-section {
    display: none;
    animation: fadeIn 0.5s ease-in;
}

.form-section.active {
    display: block;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.section-title {
    font-size: 20px;
    font-weight: bold;
    color: #333;
    margin-bottom: 25px;
    padding-bottom: 15px;
    border-bottom: 2px solid #f0f0f0;
    display: flex;
    align-items: center;
    gap: 12px;
}

.section-icon {
    color: #667eea;
    font-size: 24px;
}

.form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
}

.form-group {
    margin-bottom: 25px;
}

.form-group.full-width {
    grid-column: 1 / -1;
}

.form-label {
    font-weight: 600;
    margin-bottom: 8px;
    color: #333;
    display: block;
}

.required {
    color: #e74c3c;
}

.form-control-wrapper input,
.form-control-wrapper select,
.form-control-wrapper textarea {
    width: 100%;
    padding: 12px 15px;
    border: 2px solid #e0e0e0;
    border-radius: 10px;
    font-size: 15px;
    transition: all 0.3s;
    background: #f9f9f9;
}

.form-control-wrapper input:focus,
.form-control-wrapper select:focus,
.form-control-wrapper textarea:focus {
    border-color: #667eea;
    background: white;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    outline: none;
}

.checkbox-group {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 10px;
}

.checkbox-group label {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    padding: 8px;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    transition: all 0.3s;
}

.checkbox-group label:hover {
    background: #f0f0ff;
    border-color: #667eea;
}

.form-navigation {
    display: flex;
    justify-content: center;
    gap: 15px;
    margin-top: 40px;
    padding-top: 30px;
    border-top: 2px solid #f0f0f0;
}

.btn {
    padding: 12px 30px;
    border-radius: 10px;
    font-weight: 600;
    font-size: 16px;
    border: none;
    cursor: pointer;
    transition: all 0.3s;
    display: inline-flex;
    align-items: center;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
    background: #6c757d;
    color: white;
}

.btn-secondary:hover {
    background: #5a6268;
}

.btn-success {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    color: white;
}

.btn-success:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(40, 167, 69, 0.4);
}
</style>
{% endblock %}

{% block extra_js %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('propertyForm');
    const sections = document.querySelectorAll('.form-section');
    const progressSteps = document.querySelectorAll('.progress-step');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    
    let currentStep = 1;
    const totalSteps = sections.length;
    
    function validateStep(step) {
        const section = document.querySelector(`.form-section[data-section="${step}"]`);
        const requiredFields = section.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.style.borderColor = '#e74c3c';
                isValid = false;
            } else {
                field.style.borderColor = '#e0e0e0';
            }
        });
        
        return isValid;
    }
    
    nextBtn.addEventListener('click', function() {
        if (validateStep(currentStep)) {
            sections[currentStep - 1].classList.remove('active');
            progressSteps[currentStep - 1].classList.remove('active');
            
            currentStep++;
            
            sections[currentStep - 1].classList.add('active');
            progressSteps[currentStep - 1].classList.add('active');
            
            if (currentStep === totalSteps) {
                nextBtn.style.display = 'none';
                submitBtn.style.display = 'inline-flex';
            }
            
            if (currentStep > 1) {
                prevBtn.style.display = 'inline-flex';
            }
        }
    });
    
    prevBtn.addEventListener('click', function() {
        sections[currentStep - 1].classList.remove('active');
        progressSteps[currentStep - 1].classList.remove('active');
        
        currentStep--;
        
        sections[currentStep - 1].classList.add('active');
        progressSteps[currentStep - 1].classList.add('active');
        
        if (currentStep < totalSteps) {
            nextBtn.style.display = 'inline-flex';
            submitBtn.style.display = 'none';
        }
        
        if (currentStep === 1) {
            prevBtn.style.display = 'none';
        }
    });
});
</script>
{% endblock %}
'''

        # Create the template file
        templates_dir = os.path.join(settings.BASE_DIR, 'templates', 'properties')
        os.makedirs(templates_dir, exist_ok=True)
        
        template_path = os.path.join(templates_dir, 'enhanced_property_form.html')
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        self.stdout.write(
            self.style.SUCCESS(f'Enhanced property form template created: {template_path}')
        )
        self.stdout.write('The template includes all new fields organized in 5 steps:')
        self.stdout.write('1. Basic Information')
        self.stdout.write('2. Location and Area')
        self.stdout.write('3. Details and Features')
        self.stdout.write('4. Documents and Legal')
        self.stdout.write('5. Pricing and Publishing')