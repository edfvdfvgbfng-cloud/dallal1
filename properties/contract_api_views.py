"""
API Views للعقود العقارية
واجهات برمجة التطبيقات للعقود
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
import json

from .models import RealEstateContract, ContractParty, ContractDocument, ContractAuditLog
from .forms import RealEstateContractForm, ContractDocumentForm, ContractPartyForm


@csrf_exempt
@require_http_methods(["GET"])
@login_required
def api_contracts_list(request):
    """API: قائمة العقود"""
    
    # فحص الصلاحيات
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'}, status=403)
    
    # الاستعلام الأساسي
    contracts = RealEstateContract.objects.filter(is_archived=False)
    
    # تطبيق الفلاتر
    contract_type = request.GET.get('contract_type')
    status = request.GET.get('status')
    search = request.GET.get('search')
    
    if contract_type:
        contracts = contracts.filter(contract_type=contract_type)
    if status:
        contracts = contracts.filter(status=status)
    if search:
        contracts = contracts.filter(
            Q(contract_number__icontains=search) |
            Q(contract_title__icontains=search) |
            Q(second_party_name__icontains=search)
        )
    
    # الترتيب
    contracts = contracts.order_by('-created_at')
    
    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 25))
    paginator = Paginator(contracts, per_page)
    page_obj = paginator.get_page(page)
    
    # تحويل البيانات
    contracts_data = []
    for contract in page_obj:
        contracts_data.append({
            'id': contract.id,
            'contract_number': contract.contract_number,
            'contract_title': contract.contract_title,
            'contract_type': contract.contract_type,
            'contract_type_display': contract.get_contract_type_display(),
            'status': contract.status,
            'status_display': contract.get_status_display(),
            'amount': str(contract.amount),
            'currency': contract.currency,
            'start_date': contract.start_date.isoformat() if contract.start_date else None,
            'end_date': contract.end_date.isoformat() if contract.end_date else None,
            'property': contract.property.title if contract.property else None,
            'property_id': contract.property.id if contract.property else None,
            'broker': contract.broker.display_name if contract.broker else None,
            'created_at': contract.created_at.isoformat(),
            'documents_count': contract.documents.count(),
            'expiry_status': contract.expiry_status(),
            'days_remaining': contract.days_remaining(),
        })
    
    return JsonResponse({
        'success': True,
        'contracts': contracts_data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': paginator.count,
            'total_pages': paginator.num_pages,
        }
    })


@csrf_exempt
@require_http_methods(["GET"])
@login_required
def api_contract_detail(request, contract_id):
    """API: تفاصيل عقد"""
    
    contract = RealEstateContract.objects.filter(pk=contract_id).first()
    
    if not contract:
        return JsonResponse({'success': False, 'error': 'العقد غير موجود'}, status=404)
    
    # فحص الصلاحيات
    if not contract.can_view(request.user):
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'}, status=403)
    
    # تسجيل العرض
    ContractAuditLog.log_action(
        contract=contract,
        action='viewed',
        user=request.user,
        description='عرض تفاصيل العقد عبر API'
    )
    
    # تحويل البيانات
    contract_data = {
        'id': contract.id,
        'contract_number': contract.contract_number,
        'contract_title': contract.contract_title,
        'contract_type': contract.contract_type,
        'contract_type_display': contract.get_contract_type_display(),
        'status': contract.status,
        'status_display': contract.get_status_display(),
        'amount': str(contract.amount),
        'currency': contract.currency,
        'deposit': str(contract.deposit),
        'commission_rate': str(contract.commission_rate),
        'commission_amount': str(contract.commission_amount),
        'start_date': contract.start_date.isoformat() if contract.start_date else None,
        'end_date': contract.end_date.isoformat() if contract.end_date else None,
        'signing_date': contract.signing_date.isoformat() if contract.signing_date else None,
        'payment_frequency': contract.payment_frequency,
        'payment_frequency_display': contract.get_payment_frequency_display(),
        'payment_terms': contract.payment_terms,
        'terms_and_conditions': contract.terms_and_conditions,
        'special_clauses': contract.special_clauses,
        'renewal_clause': contract.renewal_clause,
        'termination_clause': contract.termination_clause,
        'notes': contract.notes,
        
        # الأطراف
        'property': {
            'id': contract.property.id,
            'title': contract.property.title,
            'slug': contract.property.slug,
        } if contract.property else None,
        'broker': {
            'id': contract.broker.id,
            'display_name': contract.broker.display_name,
        } if contract.broker else None,
        'client': {
            'id': contract.client.id,
            'username': contract.client.username,
        } if contract.client else None,
        'second_party_name': contract.second_party_name,
        'second_party_phone': contract.second_party_phone,
        'second_party_email': contract.second_party_email,
        
        # معلومات النظام
        'created_by': contract.created_by.username if contract.created_by else None,
        'created_at': contract.created_at.isoformat(),
        'updated_at': contract.updated_at.isoformat(),
        'is_archived': contract.is_archived,
        
        # الحالة
        'expiry_status': contract.expiry_status(),
        'days_remaining': contract.days_remaining(),
        'is_active': contract.is_active(),
        
        # الصلاحيات
        'can_view': contract.can_view(request.user),
        'can_edit': contract.can_edit(request.user),
        'can_delete': contract.can_delete(request.user),
    }
    
    # الأطراف التفصيلية
    parties_data = []
    for party in contract.parties.all():
        parties_data.append({
            'id': party.id,
            'party_type': party.party_type,
            'party_type_display': party.get_party_type_display(),
            'party_role': party.party_role,
            'party_role_display': party.get_party_role_display(),
            'full_name': party.full_name,
            'phone': party.phone,
            'national_id': party.national_id,
            'email': party.email,
            'address': party.address,
            'notes': party.notes,
        })
    contract_data['parties'] = parties_data
    
    # الوثائق
    documents_data = []
    for doc in contract.documents.all():
        documents_data.append({
            'id': doc.id,
            'document_type': doc.document_type,
            'document_type_display': doc.get_document_type_display(),
            'title': doc.title,
            'description': doc.description,
            'file_size': doc.file_size,
            'file_type': doc.file_type,
            'page_number': doc.page_number,
            'uploaded_at': doc.uploaded_at.isoformat(),
            'uploaded_by': doc.uploaded_by.username if doc.uploaded_by else None,
        })
    contract_data['documents'] = documents_data
    
    return JsonResponse({'success': True, 'contract': contract_data})


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def api_contract_create(request):
    """API: إنشاء عقد جديد"""
    
    # فحص الصلاحيات
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'}, status=403)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'بيانات غير صالحة'}, status=400)
    
    form = RealEstateContractForm(data)
    
    if form.is_valid():
        contract = form.save(commit=False)
        contract.created_by = request.user
        contract.save()
        
        return JsonResponse({
            'success': True,
            'contract': {
                'id': contract.id,
                'contract_number': contract.contract_number,
                'contract_type': contract.contract_type,
                'status': contract.status,
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def api_contract_update(request, contract_id):
    """API: تعديل عقد"""
    
    contract = RealEstateContract.objects.filter(pk=contract_id).first()
    
    if not contract:
        return JsonResponse({'success': False, 'error': 'العقد غير موجود'}, status=404)
    
    # فحص الصلاحيات
    if not contract.can_edit(request.user):
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'}, status=403)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'بيانات غير صالحة'}, status=400)
    
    form = RealEstateContractForm(data, instance=contract)
    
    if form.is_valid():
        # تسجيل التغييرات
        old_values = {
            'status': contract.status,
            'amount': str(contract.amount),
        }
        
        updated_contract = form.save()
        
        new_values = {
            'status': updated_contract.status,
            'amount': str(updated_contract.amount),
        }
        
        ContractAuditLog.log_action(
            contract=updated_contract,
            action='updated',
            user=request.user,
            old_values=old_values,
            new_values=new_values,
            description='تعديل العقد عبر API'
        )
        
        return JsonResponse({
            'success': True,
            'contract': {
                'id': updated_contract.id,
                'contract_number': updated_contract.contract_number,
                'status': updated_contract.status,
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def api_contract_archive(request, contract_id):
    """API: أرشفة عقد"""
    
    contract = RealEstateContract.objects.filter(pk=contract_id).first()
    
    if not contract:
        return JsonResponse({'success': False, 'error': 'العقد غير موجود'}, status=404)
    
    # فحص الصلاحيات
    if not contract.can_edit(request.user):
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'}, status=403)
    
    try:
        data = json.loads(request.body)
        reason = data.get('reason', '')
    except json.JSONDecodeError:
        reason = ''
    
    contract.archive(user=request.user, reason=reason)
    
    return JsonResponse({'success': True, 'message': 'تم أرشفة العقد بنجاح'})


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def api_contract_restore(request, contract_id):
    """API: استرجاع عقد من الأرشيف"""
    
    contract = RealEstateContract.objects.filter(pk=contract_id).first()
    
    if not contract:
        return JsonResponse({'success': False, 'error': 'العقد غير موجود'}, status=404)
    
    # فحص الصلاحيات
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'}, status=403)
    
    contract.restore(user=request.user)
    
    return JsonResponse({'success': True, 'message': 'تم استرجاع العقد بنجاح'})


@csrf_exempt
@require_http_methods(["GET"])
@login_required
def api_contract_statistics(request):
    """API: إحصائيات العقود"""
    
    # فحص الصلاحيات
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'}, status=403)
    
    stats = {
        'total_contracts': RealEstateContract.objects.filter(is_archived=False).count(),
        'active_contracts': RealEstateContract.objects.filter(status='active', is_archived=False).count(),
        'completed_contracts': RealEstateContract.objects.filter(status='completed', is_archived=False).count(),
        'draft_contracts': RealEstateContract.objects.filter(status='draft', is_archived=False).count(),
        'pending_contracts': RealEstateContract.objects.filter(status='pending', is_archived=False).count(),
        
        'sale_contracts': RealEstateContract.objects.filter(contract_type='sale', is_archived=False).count(),
        'rent_contracts': RealEstateContract.objects.filter(contract_type='rent', is_archived=False).count(),
        'lease_contracts': RealEstateContract.objects.filter(contract_type='lease', is_archived=False).count(),
        
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
        
        'total_value': str(RealEstateContract.objects.filter(is_archived=False).aggregate(
            total=Sum('amount')
        )['total'] or 0),
        'active_value': str(RealEstateContract.objects.filter(status='active', is_archived=False).aggregate(
            total=Sum('amount')
        )['total'] or 0),
        
        'total_documents': ContractDocument.objects.count(),
        'total_parties': ContractParty.objects.count(),
    }
    
    return JsonResponse({'success': True, 'stats': stats})


@csrf_exempt
@require_http_methods(["GET"])
@login_required
def api_expiring_contracts(request):
    """API: العقود القريبة من الانتهاء"""
    
    # فحص الصلاحيات
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'}, status=403)
    
    days = int(request.GET.get('days', 7))
    
    contracts = RealEstateContract.objects.filter(
        status='active',
        is_archived=False,
        end_date__lte=timezone.now() + timezone.timedelta(days=days),
        end_date__gte=timezone.now()
    ).order_by('end_date')
    
    contracts_data = []
    for contract in contracts:
        contracts_data.append({
            'id': contract.id,
            'contract_number': contract.contract_number,
            'contract_title': contract.contract_title,
            'contract_type': contract.contract_type,
            'contract_type_display': contract.get_contract_type_display(),
            'amount': str(contract.amount),
            'currency': contract.currency,
            'end_date': contract.end_date.isoformat(),
            'days_remaining': contract.days_remaining(),
            'expiry_status': contract.expiry_status(),
            'property': contract.property.title if contract.property else None,
        })
    
    return JsonResponse({
        'success': True,
        'contracts': contracts_data,
        'count': len(contracts_data)
    })
