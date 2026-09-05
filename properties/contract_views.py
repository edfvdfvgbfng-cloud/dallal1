"""
Views للعقود العقارية
نظام إدارة العقود والاتفاقيات العقارية المتكامل
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.files.storage import default_storage
import os

from .models import RealEstateContract, ContractParty, ContractDocument, ContractAuditLog, ContractPayment, ContractReminder
from .forms import RealEstateContractForm, ContractPartyForm, ContractDocumentForm, ContractSearchForm, ContractPaymentForm, ContractReminderForm


@login_required
def contract_list(request):
    """قائمة العقود مع البحث والتصفية"""
    
    # فحص الصلاحيات
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية للوصول إلى العقود')
        return redirect('home')
    
    # نموذج البحث
    search_form = ContractSearchForm(request.GET)
    
    # الاستعلام الأساسي - استبعاد العقود المؤرشفة افتراضياً
    contracts = RealEstateContract.objects.filter(is_archived=False)
    
    # تطبيق الفلاتر
    if search_form.is_valid():
        q = search_form.cleaned_data.get('q')
        contract_type = search_form.cleaned_data.get('contract_type')
        duration_type = search_form.cleaned_data.get('duration_type')
        status = search_form.cleaned_data.get('status')
        currency = search_form.cleaned_data.get('currency')
        governorate = search_form.cleaned_data.get('governorate')
        start_date_from = search_form.cleaned_data.get('start_date_from')
        start_date_to = search_form.cleaned_data.get('start_date_to')
        end_date_from = search_form.cleaned_data.get('end_date_from')
        end_date_to = search_form.cleaned_data.get('end_date_to')
        amount_min = search_form.cleaned_data.get('amount_min')
        amount_max = search_form.cleaned_data.get('amount_max')
        is_archived = search_form.cleaned_data.get('is_archived')
        
        # البحث النصي
        if q:
            contracts = contracts.filter(
                Q(contract_number__icontains=q) |
                Q(contract_title__icontains=q) |
                Q(second_party_name__icontains=q) |
                Q(second_party_phone__icontains=q) |
                Q(property__title__icontains=q)
            )
        
        # الفلاتر المحددة
        if contract_type:
            contracts = contracts.filter(contract_type=contract_type)
        if duration_type:
            contracts = contracts.filter(duration_type=duration_type)
        if status:
            contracts = contracts.filter(status=status)
        if currency:
            contracts = contracts.filter(currency=currency)
        if governorate:
            contracts = contracts.filter(property__governorate=governorate)
        if start_date_from:
            contracts = contracts.filter(start_date__gte=start_date_from)
        if start_date_to:
            contracts = contracts.filter(start_date__lte=start_date_to)
        if end_date_from:
            contracts = contracts.filter(end_date__gte=end_date_from)
        if end_date_to:
            contracts = contracts.filter(end_date__lte=end_date_to)
        if amount_min:
            contracts = contracts.filter(amount__gte=amount_min)
        if amount_max:
            contracts = contracts.filter(amount__lte=amount_max)
        
        # عرض العقود المؤرشفة
        if is_archived:
            contracts = RealEstateContract.objects.filter(is_archived=True)
    
    # الترتيب
    contracts = contracts.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(contracts, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # الإحصائيات
    stats = {
        'total': RealEstateContract.objects.filter(is_archived=False).count(),
        'active': RealEstateContract.objects.filter(status='active', is_archived=False).count(),
        'completed': RealEstateContract.objects.filter(status='completed', is_archived=False).count(),
        'expiring_soon': RealEstateContract.objects.filter(
            status='active',
            is_archived=False,
            end_date__lte=timezone.now() + timezone.timedelta(days=7)
        ).count(),
        'total_value': RealEstateContract.objects.filter(is_archived=False).aggregate(
            total=Sum('amount')
        )['total'] or 0,
    }
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'stats': stats,
    }
    
    return render(request, 'properties/contracts/contract_list.html', context)


@login_required
def contract_detail(request, contract_id):
    """عرض تفاصيل العقد"""
    
    contract = get_object_or_404(RealEstateContract, pk=contract_id)
    
    # فحص الصلاحيات
    if not contract.can_view(request.user):
        return HttpResponseForbidden('ليس لديك صلاحية لعرض هذا العقد')
    
    # تسجيل العرض في Audit Log
    ContractAuditLog.log_action(
        contract=contract,
        action='viewed',
        user=request.user,
        description=f'عرض تفاصيل العقد {contract.contract_number}'
    )
    
    # جلب البيانات المرتبطة
    parties = contract.parties.all()
    documents = contract.documents.all()
    payments = contract.payments.all()
    reminders = contract.reminders.filter(is_sent=False)
    audit_logs = contract.audit_logs.all()[:20]  # آخر 20 عملية
    
    # حساب حالة الانتهاء
    expiry_status = contract.expiry_status()
    days_remaining = contract.days_remaining()
    
    context = {
        'contract': contract,
        'parties': parties,
        'documents': documents,
        'payments': payments,
        'reminders': reminders,
        'audit_logs': audit_logs,
        'expiry_status': expiry_status,
        'days_remaining': days_remaining,
        'can_edit': contract.can_edit(request.user),
        'can_delete': contract.can_delete(request.user),
    }
    
    return render(request, 'properties/contracts/contract_detail.html', context)


@login_required
def contract_create(request):
    """إنشاء عقد جديد"""
    
    # فحص الصلاحيات
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, 'ليس لديك صلاحية لإنشاء عقود')
        return redirect('contract_list')
    
    if request.method == 'POST':
        form = RealEstateContractForm(request.POST, request.FILES)
        if form.is_valid():
            contract = form.save(commit=False)
            contract.created_by = request.user
            contract.save()

            # معالجة الصور المرفوعة
            contract_images = request.FILES.getlist('contract_images')
            for idx, image in enumerate(contract_images):
                # التحقق من نوع الملف
                if not image.content_type.startswith('image/') and image.content_type != 'application/pdf':
                    messages.warning(request, f'تم تجاهل الملف {image.name} - النوع غير مدعوم')
                    continue
                
                # التحقق من الحجم (10MB)
                if image.size > 10 * 1024 * 1024:
                    messages.warning(request, f'تم تجاهل الملف {image.name} - الحجم يتجاوز 10MB')
                    continue
                
                # إنشاء وثيقة للصورة
                file_type = 'image' if image.content_type.startswith('image/') else 'document'
                ContractDocument.objects.create(
                    contract=contract,
                    file=image,
                    file_type=file_type,
                    page_number=idx + 1,
                    uploaded_by=request.user
                )

            # تسجيل العملية في Audit Log
            ContractAuditLog.objects.create(
                contract=contract,
                performed_by=request.user,
                action='create',
                description=f'إنشاء عقد جديد: {contract.contract_number}'
            )
            
            messages.success(request, f'تم إنشاء العقد {contract.contract_number} بنجاح')
            return redirect('contract_detail', contract_id=contract.id)
    else:
        form = RealEstateContractForm()
    
    # اختيار نوع العقد مسبقاً إذا تم تحديده
    contract_type = request.GET.get('type')
    if contract_type:
        form.fields['contract_type'].initial = contract_type
    
    context = {
        'form': form,
        'contract_type': contract_type,
    }
    
    return render(request, 'properties/contracts/contract_form.html', context)


@login_required
def contract_edit(request, contract_id):
    """تعديل عقد موجود"""
    
    contract = get_object_or_404(RealEstateContract, pk=contract_id)
    
    # فحص الصلاحيات
    if not contract.can_edit(request.user):
        return HttpResponseForbidden('ليس لديك صلاحية لتعديل هذا العقد')
    
    if request.method == 'POST':
        form = RealEstateContractForm(request.POST, instance=contract)
        if form.is_valid():
            # تسجيل التغييرات في Audit Log
            old_values = {
                'contract_type': contract.contract_type,
                'amount': str(contract.amount),
                'status': contract.status,
            }
            
            updated_contract = form.save()
            
            new_values = {
                'contract_type': updated_contract.contract_type,
                'amount': str(updated_contract.amount),
                'status': updated_contract.status,
            }
            
            ContractAuditLog.log_action(
                contract=updated_contract,
                action='updated',
                user=request.user,
                old_values=old_values,
                new_values=new_values,
                description='تعديل بيانات العقد'
            )
            
            messages.success(request, 'تم تحديث العقد بنجاح')
            return redirect('contract_detail', contract_id=contract.id)
    else:
        form = RealEstateContractForm(instance=contract)
    
    context = {
        'form': form,
        'contract': contract,
    }
    
    return render(request, 'properties/contracts/contract_form.html', context)


@login_required
@require_POST
def contract_archive(request, contract_id):
    """أرشفة عقد (Soft Delete)"""
    
    contract = get_object_or_404(RealEstateContract, pk=contract_id)
    
    # فحص الصلاحيات
    if not contract.can_edit(request.user):
        return HttpResponseForbidden('ليس لديك صلاحية لأرشفة هذا العقد')
    
    reason = request.POST.get('reason', '')
    contract.archive(user=request.user, reason=reason)
    
    messages.success(request, 'تم أرشفة العقد بنجاح')
    return redirect('contract_list')


@login_required
@require_POST
def contract_restore(request, contract_id):
    """استرجاع عقد من الأرشيف"""
    
    contract = get_object_or_404(RealEstateContract, pk=contract_id)
    
    # فحص الصلاحيات
    if not request.user.is_superuser:
        return HttpResponseForbidden('ليس لديك صلاحية لاسترجاع العقود')
    
    contract.restore(user=request.user)
    
    messages.success(request, 'تم استرجاع العقد بنجاح')
    return redirect('contract_list')


@login_required
@require_POST
def contract_delete(request, contract_id):
    """حذف عقد نهائياً (للمسؤولين فقط)"""
    
    contract = get_object_or_404(RealEstateContract, pk=contract_id)
    
    # فحص الصلاحيات
    if not contract.can_delete(request.user):
        return HttpResponseForbidden('ليس لديك صلاحية لحذف هذا العقد')
    
    contract_number = contract.contract_number
    
    # تسجيل الحذف في Audit Log
    ContractAuditLog.log_action(
        contract=contract,
        action='deleted',
        user=request.user,
        description=f'حذف العقد {contract_number} نهائياً'
    )
    
    contract.delete()
    
    messages.success(request, f'تم حذف العقد {contract_number} نهائياً')
    return redirect('contract_list')


@login_required
def contract_status_change(request, contract_id, new_status):
    """تغيير حالة العقد"""
    
    contract = get_object_or_404(RealEstateContract, pk=contract_id)
    
    # فحص الصلاحيات
    if not contract.can_edit(request.user):
        return HttpResponseForbidden('ليس لديك صلاحية لتغيير حالة هذا العقد')
    
    old_status = contract.status
    contract.status = new_status
    contract.save()
    
    # تسجيل التغيير في Audit Log
    ContractAuditLog.log_action(
        contract=contract,
        action='status_changed',
        user=request.user,
        old_values={'status': old_status},
        new_values={'status': new_status},
        description=f'تغيير حالة العقد من {old_status} إلى {new_status}'
    )
    
    messages.success(request, 'تم تغيير حالة العقد بنجاح')
    return redirect('contract_detail', contract_id=contract.id)


@login_required
def contract_document_add(request, contract_id):
    """إضافة وثيقة للعقد"""
    
    contract = get_object_or_404(RealEstateContract, pk=contract_id)
    
    # فحص الصلاحيات
    if not contract.can_edit(request.user):
        return HttpResponseForbidden('ليس لديك صلاحية لإضافة وثائق لهذا العقد')
    
    if request.method == 'POST':
        form = ContractDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.contract = contract
            document.uploaded_by = request.user
            
            # تحديد رقم الصفحة تلقائياً
            last_page = contract.documents.count()
            document.page_number = last_page + 1
            
            document.save()
            
            messages.success(request, 'تم إضافة الوثيقة بنجاح')
            return redirect('contract_detail', contract_id=contract.id)
    else:
        form = ContractDocumentForm()
    
    context = {
        'form': form,
        'contract': contract,
    }
    
    return render(request, 'properties/contracts/document_form.html', context)


@login_required
@require_POST
def contract_document_delete(request, document_id):
    """حذف وثيقة من العقد"""
    
    document = get_object_or_404(ContractDocument, pk=document_id)
    contract = document.contract
    
    # فحص الصلاحيات
    if not document.can_delete(request.user):
        return HttpResponseForbidden('ليس لديك صلاحية لحذف هذه الوثيقة')
    
    # حذف الملف من التخزين
    if document.file:
        if default_storage.exists(document.file.name):
            default_storage.delete(document.file.name)
    
    # تسجيل الحذف في Audit Log
    ContractAuditLog.log_action(
        contract=contract,
        action='document_removed',
        user=request.user,
        description=f'حذف الوثيقة: {document.title}'
    )
    
    document.delete()
    
    messages.success(request, 'تم حذف الوثيقة بنجاح')
    return redirect('contract_detail', contract_id=contract.id)


@login_required
def contract_document_view(request, document_id):
    """عرض ملف وثيقة العقد"""
    
    document = get_object_or_404(ContractDocument, pk=document_id)
    
    # فحص الصلاحيات
    if not document.can_view(request.user):
        return HttpResponseForbidden('ليس لديك صلاحية لعرض هذه الوثيقة')
    
    # تسجيل العرض في Audit Log
    ContractAuditLog.log_action(
        contract=document.contract,
        action='viewed',
        user=request.user,
        description=f'عرض الوثيقة: {document.title}'
    )
    
    # إرجاع الملف
    if document.file:
        response = HttpResponse(document.file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'inline; filename="{document.title}"'
        return response
    
    return HttpResponseForbidden('الملف غير موجود')


@login_required
def contract_party_add(request, contract_id):
    """إضافة طرف للعقد"""
    
    contract = get_object_or_404(RealEstateContract, pk=contract_id)
    
    # فحص الصلاحيات
    if not contract.can_edit(request.user):
        return HttpResponseForbidden('ليس لديك صلاحية لإضافة أطراف لهذا العقد')
    
    if request.method == 'POST':
        form = ContractPartyForm(request.POST)
        if form.is_valid():
            party = form.save(commit=False)
            party.contract = contract
            party.save()
            
            # تسجيل الإضافة في Audit Log
            ContractAuditLog.log_action(
                contract=contract,
                action='party_added',
                user=request.user,
                description=f'إضافة طرف {party.get_party_type_display()}: {party.full_name}'
            )
            
            messages.success(request, 'تم إضافة الطرف بنجاح')
            return redirect('contract_detail', contract_id=contract.id)
    else:
        form = ContractPartyForm()
    
    context = {
        'form': form,
        'contract': contract,
    }
    
    return render(request, 'properties/contracts/party_form.html', context)


@login_required
def contract_statistics(request):
    """إحصائيات العقود للوحة التحكم"""
    
    # فحص الصلاحيات
    if not request.user.is_superuser and not request.user.is_staff:
        return HttpResponseForbidden('ليس لديك صلاحية لعرض الإحصائيات')
    
    # الإحصائيات الأساسية
    stats = {
        'total_contracts': RealEstateContract.objects.filter(is_archived=False).count(),
        'active_contracts': RealEstateContract.objects.filter(status='active', is_archived=False).count(),
        'completed_contracts': RealEstateContract.objects.filter(status='completed', is_archived=False).count(),
        'draft_contracts': RealEstateContract.objects.filter(status='draft', is_archived=False).count(),
        'pending_contracts': RealEstateContract.objects.filter(status='pending', is_archived=False).count(),
        
        # حسب النوع
        'sale_contracts': RealEstateContract.objects.filter(contract_type='sale', is_archived=False).count(),
        'rent_contracts': RealEstateContract.objects.filter(contract_type='rent', is_archived=False).count(),
        'lease_contracts': RealEstateContract.objects.filter(contract_type='lease', is_archived=False).count(),
        
        # العقود القريبة من الانتهاء
        'expiring_7_days': RealEstateContract.objects.filter(
            status='active',
            is_archived=False,
            end_date__lte=timezone.now() + timezone.timedelta(days=7),
            end_date__gte=timezone.now()
        ).count(),
        'expiring_30_days': RealEstateContract.objects.filter(
            status='active',
            is_archived=False,
            end_date__lte=timezone.now() + timezone.timedelta(days=30),
            end_date__gte=timezone.now()
        ).count(),
        
        # القيمة المالية
        'total_value': RealEstateContract.objects.filter(is_archived=False).aggregate(
            total=Sum('amount')
        )['total'] or 0,
        'active_value': RealEstateContract.objects.filter(status='active', is_archived=False).aggregate(
            total=Sum('amount')
        )['total'] or 0,
        
        # الوثائق
        'total_documents': ContractDocument.objects.count(),
        
        # الأطراف
        'total_parties': ContractParty.objects.count(),
    }
    
    # العقود القريبة من الانتهاء للعرض
    expiring_contracts = RealEstateContract.objects.filter(
        status='active',
        is_archived=False,
        end_date__lte=timezone.now() + timezone.timedelta(days=7),
        end_date__gte=timezone.now()
    ).order_by('end_date')[:10]
    
    context = {
        'stats': stats,
        'expiring_contracts': expiring_contracts,
    }
    
    return render(request, 'properties/contracts/contract_statistics.html', context)


@login_required
def property_contracts(request, property_id):
    """عرض العقود المرتبطة بعقار معين"""
    
    from .models import Property
    property_obj = get_object_or_404(Property, pk=property_id)
    
    # فحص الصلاحيات
    if not request.user.is_superuser and not request.user.is_staff:
        return HttpResponseForbidden('ليس لديك صلاحية لعرض عقود هذا العقار')
    
    contracts = RealEstateContract.objects.filter(
        property=property_obj,
        is_archived=False
    ).order_by('-created_at')
    
    context = {
        'property': property_obj,
        'contracts': contracts,
    }
    
    return render(request, 'properties/contracts/property_contracts.html', context)


@login_required
def contract_copy(request, contract_id):
    """نسخ عقد لإنشاء عقد جديد مشابه"""
    
    original_contract = get_object_or_404(RealEstateContract, pk=contract_id)
    
    # فحص الصلاحيات
    if not original_contract.can_view(request.user):
        return HttpResponseForbidden('ليس لديك صلاحية لنسخ هذا العقد')
    
    if request.method == 'POST':
        form = RealEstateContractForm(request.POST)
        if form.is_valid():
            new_contract = form.save(commit=False)
            new_contract.created_by = request.user
            new_contract.contract_number = new_contract.generate_contract_number()
            new_contract.save()
            
            # نسخ الوثائق
            for doc in original_contract.documents.all():
                ContractDocument.objects.create(
                    contract=new_contract,
                    file=doc.file,
                    file_type=doc.file_type,
                    title=doc.title,
                    page_number=doc.page_number,
                    uploaded_by=request.user
                )
            
            # نسخ الأطراف
            for party in original_contract.parties.all():
                ContractParty.objects.create(
                    contract=new_contract,
                    party_type=party.party_type,
                    full_name=party.full_name,
                    phone=party.phone,
                    email=party.email,
                    address=party.address,
                    national_id=party.national_id
                )
            
            # تسجيل النسخ في Audit Log
            ContractAuditLog.log_action(
                contract=new_contract,
                action='created',
                user=request.user,
                description=f'نسخ من العقد {original_contract.contract_number}'
            )
            
            messages.success(request, f'تم نسخ العقد بنجاح. الرقم الجديد: {new_contract.contract_number}')
            return redirect('contract_detail', contract_id=new_contract.id)
    else:
        # Pre-fill form with original contract data
        initial_data = {
            'contract_type': original_contract.contract_type,
            'duration_type': original_contract.duration_type,
            'currency': original_contract.currency,
            'payment_frequency': original_contract.payment_frequency,
            'property': original_contract.property,
            'broker': original_contract.broker,
            'commission_rate': original_contract.commission_rate,
            'terms_and_conditions': original_contract.terms_and_conditions,
            'special_clauses': original_contract.special_clauses,
            'renewal_clause': original_contract.renewal_clause,
            'termination_clause': original_contract.termination_clause,
        }
        form = RealEstateContractForm(initial=initial_data)
    
    context = {
        'form': form,
        'original_contract': original_contract,
    }
    
    return render(request, 'properties/contracts/contract_copy.html', context)


@login_required
def contract_bulk_actions(request):
    """إجراءات جماعية على العقود"""
    
    # فحص الصلاحيات
    if not request.user.is_superuser and not request.user.is_staff:
        return HttpResponseForbidden('ليس لديك صلاحية لتنفيذ إجراءات جماعية')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        contract_ids = request.POST.getlist('contract_ids')
        
        if not contract_ids:
            messages.error(request, 'لم يتم اختيار أي عقود')
            return redirect('contract_list')
        
        contracts = RealEstateContract.objects.filter(id__in=contract_ids)
        
        if action == 'archive':
            for contract in contracts:
                contract.archive(user=request.user, reason='أرشفة جماعية')
            messages.success(request, f'تم أرشفة {len(contracts)} عقد بنجاح')
        
        elif action == 'activate':
            for contract in contracts:
                contract.mark_as_active(user=request.user)
            messages.success(request, f'تم تفعيل {len(contracts)} عقد بنجاح')
        
        elif action == 'complete':
            for contract in contracts:
                contract.mark_as_completed(user=request.user)
            messages.success(request, f'تم إكمال {len(contracts)} عقد بنجاح')
        
        elif action == 'terminate':
            for contract in contracts:
                contract.mark_as_terminated(user=request.user)
            messages.success(request, f'تم إنهاء {len(contracts)} عقد بنجاح')
        
        elif action == 'delete':
            for contract in contracts:
                if contract.can_delete(request.user):
                    contract.delete()
            messages.success(request, f'تم حذف {len(contracts)} عقد بنجاح')
        
        return redirect('contract_list')
    
    return redirect('contract_list')


@login_required
def contract_timeline(request, contract_id):
    """عرض جدول زمني للعقد وتغييراته"""
    
    contract = get_object_or_404(RealEstateContract, pk=contract_id)
    
    # فحص الصلاحيات
    if not contract.can_view(request.user):
        return HttpResponseForbidden('ليس لديك صلاحية لعرض جدول هذا العقد')
    
    # جلب سجل التدقيق والمدفوعات
    audit_logs = contract.audit_logs.all().order_by('created_at')
    payments = contract.payments.all().order_by('payment_date')
    
    # دمج الأحداث في جدول زمني واحد
    timeline_events = []
    
    for log in audit_logs:
        timeline_events.append({
            'date': log.created_at,
            'type': 'audit',
            'title': log.get_action_display(),
            'description': log.description,
            'user': log.performed_by.username if log.performed_by else 'System',
            'icon': '📝'
        })
    
    for payment in payments:
        timeline_events.append({
            'date': payment.payment_date or payment.created_at,
            'type': 'payment',
            'title': f'دفعة {payment.payment_number}',
            'description': f'{payment.amount} {payment.currency} - {payment.get_payment_status_display()}',
            'user': payment.processed_by.username if payment.processed_by else '-',
            'icon': '💰'
        })
    
    # إضافة أحداث العقد الرئيسية
    if contract.created_at:
        timeline_events.append({
            'date': contract.created_at,
            'type': 'contract',
            'title': 'إنشاء العقد',
            'description': f'عقد {contract.contract_number}',
            'user': contract.created_by.username if contract.created_by else '-',
            'icon': '📄'
        })
    
    if contract.signing_date:
        timeline_events.append({
            'date': contract.signing_date,
            'type': 'contract',
            'title': 'توقيع العقد',
            'description': 'تم توقيع العقد',
            'user': '-',
            'icon': '✍️'
        })
    
    if contract.approved_at:
        timeline_events.append({
            'date': contract.approved_at,
            'type': 'contract',
            'title': 'موافقة على العقد',
            'description': 'تمت الموافقة على العقد',
            'user': contract.approved_by.username if contract.approved_by else '-',
            'icon': '✅'
        })
    
    # ترتيب الأحداث حسب التاريخ
    timeline_events.sort(key=lambda x: x['date'], reverse=True)
    
    context = {
        'contract': contract,
        'timeline_events': timeline_events,
    }
    
    return render(request, 'properties/contracts/contract_timeline.html', context)


@login_required
def contract_reminders(request, contract_id):
    """إدارة تذكيرات العقد"""
    
    contract = get_object_or_404(RealEstateContract, pk=contract_id)
    
    # فحص الصلاحيات
    if not contract.can_edit(request.user):
        return HttpResponseForbidden('ليس لديك صلاحية لإدارة تذكيرات هذا العقد')
    
    if request.method == 'POST':
        form = ContractReminderForm(request.POST)
        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.contract = contract
            reminder.created_by = request.user
            reminder.save()
            
            messages.success(request, 'تم إضافة التذكير بنجاح')
            return redirect('contract_detail', contract_id=contract.id)
    else:
        form = ContractReminderForm()
    
    reminders = contract.reminders.all().order_by('reminder_date')
    
    context = {
        'contract': contract,
        'form': form,
        'reminders': reminders,
    }
    
    return render(request, 'properties/contracts/contract_reminders.html', context)
