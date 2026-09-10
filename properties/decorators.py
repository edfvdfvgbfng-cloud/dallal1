"""
Decorators للحماية على الوصول حسب نوع المستخدم
Access Control Decorators based on User Type
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

from .permissions import get_user_type, can_manage_brokers


def user_required(view_func):
    """
    Decorator للتحقق من أن المستخدم هو USER فقط
    """
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type != 'user':
            messages.error(request, 'هذه الصفحة متاحة للمستخدمين العاديين فقط')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapped_view


def broker_required(view_func):
    """
    Decorator للتحقق من أن المستخدم هو BROKER فقط
    """
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type != 'broker':
            messages.error(request, 'هذه الصفحة متاحة للدلالين فقط')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapped_view


def admin_required(view_func):
    """
    Decorator للتحقق من أن المستخدم هو ADMIN فقط
    """
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type != 'admin':
            messages.error(request, 'هذه الصفحة متاحة للإدارة فقط')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapped_view


def admin_or_broker_required(view_func):
    """
    Decorator للتحقق من أن المستخدم هو ADMIN أو BROKER
    """
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type not in ['admin', 'broker']:
            messages.error(request, 'هذه الصفحة متاحة للإدارة والدلالين فقط')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapped_view


def broker_or_user_required(view_func):
    """
    Decorator للتحقق من أن المستخدم هو BROKER أو USER
    """
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        user_type = get_user_type(request.user)
        if user_type not in ['broker', 'user']:
            messages.error(request, 'هذه الصفحة متاحة للدلالين والمستخدمين فقط')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapped_view


def manage_brokers_required(view_func):
    """
    Decorator للتحقق من أن المستخدم يملك صلاحية إدارة الدلالين
    """
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if not can_manage_brokers(request.user):
            messages.error(request, 'ليس لديك صلاحية إدارة الدلالين')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapped_view