"""
Common mixins for reusing functionality across views and models.
"""

from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


class JsonResponseMixin:
    """Mixin to return JSON responses"""
    
    def render_json_response(self, data, status=200):
        return JsonResponse(data, status=status)


class PaginationMixin:
    """Mixin for paginated views"""
    
    def paginate_queryset(self, queryset, page_size=12):
        paginator = Paginator(queryset, page_size)
        page = self.request.GET.get('page', 1)
        
        try:
            paginated = paginator.page(page)
        except PageNotAnInteger:
            paginated = paginator.page(1)
        except EmptyPage:
            paginated = paginator.page(paginator.num_pages)
        
        return paginated


class AdminRequiredMixin:
    """Mixin to restrict access to admin users"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
            return self.handle_no_permission(request)
        return super().dispatch(request, *args, **kwargs)
    
    def handle_no_permission(self, request):
        from django.shortcuts import redirect
        return redirect('login')


class AjaxRequiredMixin:
    """Mixin to require AJAX requests"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'AJAX request required'}, status=400)
        return super().dispatch(request, *args, **kwargs)


class FormMixin:
    """Mixin for form handling with consistent error handling"""
    
    def form_valid(self, form):
        messages.success(self.request, 'تمت العملية بنجاح')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'حدث خطأ في النموذج. يرجى التحقق من البيانات المدخلة')
        return super().form_invalid(form)


class ContextMixin:
    """Mixin for adding common context to templates"""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'view_name': self.__class__.__name__.lower(),
            'user_can_edit': self.request.user.is_authenticated,
        })
        return context


class QueryOptimizationMixin:
    """Mixin for optimizing database queries"""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return self.optimize_queryset(queryset)
    
    def optimize_queryset(self, queryset):
        """Override this method in subclasses for specific optimizations"""
        return queryset.select_related().prefetch_related()


class CacheMixin:
    """Mixin for caching view responses"""
    
    cache_timeout = 300  # 5 minutes default
    
    def get_cache_key(self):
        """Generate a unique cache key for this view"""
        return f"{self.__class__.__name__}_{self.request.get_full_path()}"
    
    def dispatch(self, request, *args, **kwargs):
        from django.core.cache import cache
        
        cache_key = self.get_cache_key()
        cached_response = cache.get(cache_key)
        
        if cached_response:
            return cached_response
        
        response = super().dispatch(request, *args, **kwargs)
        
        if hasattr(response, 'render'):
            response = response.render()
            cache.set(cache_key, response, self.cache_timeout)
        
        return response


class LoggingMixin:
    """Mixin for logging view activities"""
    
    def log_activity(self, action, details=None):
        """Log user activity"""
        import logging
        logger = logging.getLogger('activity')
        
        log_data = {
            'user': self.request.user.username if self.request.user.is_authenticated else 'Anonymous',
            'action': action,
            'path': self.request.path,
            'method': self.request.method,
            'details': details or {},
        }
        
        logger.info(f"Activity: {log_data}")


class RateLimitMixin:
    """Mixin for rate limiting requests"""
    
    rate_limit = 100  # requests per minute
    rate_limit_period = 60  # seconds
    
    def dispatch(self, request, *args, **kwargs):
        from django.core.cache import cache
        from django.http import JsonResponse
        
        if not request.user.is_authenticated:
            client_ip = self.get_client_ip(request)
            cache_key = f"rate_limit_{client_ip}"
            
            request_count = cache.get(cache_key, 0)
            
            if request_count >= self.rate_limit:
                return JsonResponse({
                    'error': 'تم تجاوز الحد المسموح من الطلبات. يرجى المحاولة لاحقاً'
                }, status=429)
            
            cache.set(cache_key, request_count + 1, self.rate_limit_period)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    
    def soft_delete(self, request, *args, **kwargs):
        """Soft delete instead of hard delete"""
        obj = self.get_object()
        obj.is_deleted = True
        obj.deleted_at = timezone.now()
        obj.deleted_by = request.user
        obj.save()
        
        messages.success(request, 'تم الحذف بنجاح')
        return redirect(self.get_success_url())


class BulkActionMixin:
    """Mixin for handling bulk actions on querysets"""
    
    bulk_actions = ['delete', 'activate', 'deactivate']
    
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_ids')
        
        if action not in self.bulk_actions:
            messages.error(request, 'إجراء غير صالح')
            return redirect(self.get_success_url())
        
        if not selected_ids:
            messages.warning(request, 'لم يتم تحديد أي عناصر')
            return redirect(self.get_success_url())
        
        queryset = self.get_queryset().filter(id__in=selected_ids)
        
        if action == 'delete':
            count = queryset.count()
            queryset.delete()
            messages.success(request, f'تم حذف {count} عنصر بنجاح')
        elif action == 'activate':
            count = queryset.update(is_active=True)
            messages.success(request, f'تم تفعيل {count} عنصر بنجاح')
        elif action == 'deactivate':
            count = queryset.update(is_active=False)
            messages.success(request, f'تم تعطيل {count} عنصر بنجاح')
        
        return redirect(self.get_success_url())