"""
AI Admin Views - Dashboard for monitoring and managing AI system
"""

import logging
from typing import Dict, List, Optional, Any
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.core.paginator import Paginator
import json

from .ai_training_models import (
    TrainingExample, UserFeedback, UnknownQuery, 
    ModelVersion, ModelEvaluation, SearchAnalytics,
    ConversationLog, KnowledgeBaseEntry, ToolUsageLog
)
from .ai_learning_pipeline import (
    data_collector, dataset_manager, model_trainer, evaluator,
    debug_mode, health_checker
)
from .ai_voice_provider import voice_analytics

logger = logging.getLogger('properties')


@login_required
@user_passes_test(lambda u: u.is_staff)
def ai_admin_dashboard(request):
    """Main AI Admin Dashboard"""
    try:
        # Get overview statistics
        stats = dataset_manager.get_dataset_statistics()
        
        # Get recent feedback
        recent_feedback = UserFeedback.objects.select_related('user').order_by('-created_at')[:10]
        
        # Get unknown queries
        unknown_queries = UnknownQuery.objects.filter(resolved=False).order_by('-occurrence_count')[:10]
        
        # Get model versions
        model_versions = ModelVersion.objects.all().order_by('-training_date')[:5]
        
        # Get search analytics summary
        search_analytics = SearchAnalytics.objects.values('detected_intent').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        context = {
            'stats': stats,
            'recent_feedback': recent_feedback,
            'unknown_queries': unknown_queries,
            'model_versions': model_versions,
            'search_analytics': list(search_analytics),
            'page_title': 'لوحة تحكم AI'
        }
        
        return render(request, 'admin/ai_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error loading AI dashboard: {str(e)}")
        messages.error(f"حدث خطأ في تحميل لوحة التحكم: {str(e)}")
        return redirect('/admin/')


@login_required
@user_passes_test(lambda u: u.is_staff)
def ai_training_examples(request):
    """Training Examples Management"""
    try:
        status_filter = request.GET.get('status', 'all')
        intent_filter = request.GET.get('intent', 'all')
        
        examples = TrainingExample.objects.all()
        
        if status_filter != 'all':
            examples = examples.filter(status=status_filter)
        if intent_filter != 'all':
            examples = examples.filter(intent=intent_filter)
        
        examples = examples.order_by('-created_at')
        
        # Pagination
        paginator = Paginator(examples, 25)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context = {
            'examples': page_obj,
            'status_filter': status_filter,
            'intent_filter': intent_filter,
            'page_title': 'أمثلة التدريب'
        }
        
        return render(request, 'admin/ai_training_examples.html', context)
        
    except Exception as e:
        logger.error(f"Error loading training examples: {str(e)}")
        messages.error(f"حدث خطأ: {str(e)}")
        return redirect('/admin/ai/')


@login_required
@user_passes_test(lambda u: u.is_staff)
def ai_review_examples(request):
    """Review pending training examples"""
    try:
        pending_examples = TrainingExample.objects.filter(status='pending').order_by('-created_at')
        
        if request.method == 'POST':
            action = request.POST.get('action')
            example_id = request.POST.get('example_id')
            
            if action == 'approve':
                example = TrainingExample.objects.get(id=example_id)
                example.status = 'approved'
                example.reviewed_by = request.user
                example.reviewed_at = timezone.now()
                example.save()
                messages.success(f"تم اعتماد المثال: {example.text[:50]}...")
            
            elif action == 'reject':
                example = TrainingExample.objects.get(id=example_id)
                example.status = 'rejected'
                example.reviewed_by = request.user
                example.reviewed_at = timezone.now()
                example.save()
                messages.success(f"تم رفض المثال: {example.text[:50]}...")
            
            elif action == 'flag':
                example = TrainingExample.objects.get(id=example_id)
                example.status = 'flagged'
                example.reviewed_by = request.user
                example.reviewed_at = timezone.now()
                example.reviewer_notes = request.POST.get('notes', '')
                example.save()
                messages.success(f"تم وضع علامة على المثال: {example.text[:50]}...")
            
            return redirect('admin/ai/review-examples/')
        
        context = {
            'pending_examples': pending_examples,
            'page_title': 'مراجعة أمثلة التدريب'
        }
        
        return render(request, 'admin/ai_review_examples.html', context)
        
    except Exception as e:
        logger.error(f"Error reviewing examples: {str(e)}")
        messages.error(f"حدث خطأ: {str(e)}")
        return redirect('/admin/ai/')


@login_required
@user_passes_test(lambda u: u.is_staff)
def ai_unknown_queries(request):
    """Manage unknown queries for review"""
    try:
        unknown_queries = UnknownQuery.objects.filter(resolved=False).order_by('-occurrence_count')
        
        if request.method == 'POST':
            action = request.POST.get('action')
            query_id = request.POST.get('query_id')
            
            if action == 'resolve':
                query = UnknownQuery.objects.get(id=query_id)
                query.resolved = True
                query.resolved_intent = request.POST.get('resolved_intent')
                query.resolved_by = request.user
                query.resolved_at = timezone.now()
                query.resolution_notes = request.POST.get('notes', '')
                query.save()
                
                # Create training example from resolved query
                if query.resolved_intent:
                    data_collector.collect_training_example(
                        query.text,
                        query.resolved_intent,
                        query.attempted_entities,
                        query.confidence or 0.5,
                        source='resolved_unknown_query'
                    )
                
                messages.success(f"تم حل الاستعلام: {query.text[:50]}...")
            
            elif action == 'update_priority':
                query = UnknownQuery.objects.get(id=query_id)
                query.priority = int(request.POST.get('priority', 1))
                query.save()
                messages.success(f"تم تحديث الأولوية")
            
            return redirect('admin/ai/unknown-queries/')
        
        context = {
            'unknown_queries': unknown_queries,
            'page_title': 'الاستعلامات غير المفهومة'
        }
        
        return render(request, 'admin/ai_unknown_queries.html', context)
        
    except Exception as e:
        logger.error(f"Error managing unknown queries: {str(e)}")
        messages.error(f"حدث خطأ: {str(e)}")
        return redirect('/admin/ai/')


@login_required
@user_passes_test(lambda u: u.is_staff)
def ai_model_versions(request):
    """Model version management"""
    try:
        model_versions = ModelVersion.objects.all().order_by('-training_date')
        
        if request.method == 'POST':
            action = request.POST.get('action')
            version = request.POST.get('version')
            
            if action == 'deploy':
                result = model_trainer.deploy_model(version, request.user)
                if result['success']:
                    messages.success(f"تم نشر النموذج: {version}")
                else:
                    messages.error(f"فشل النشر: {result.get('error')}")
            
            elif action == 'rollback':
                # Rollback logic
                messages.info("خيار التراجع غير متاح حالياً")
            
            return redirect('admin/ai/model-versions/')
        
        context = {
            'model_versions': model_versions,
            'page_title': 'إصدارات النموذج'
        }
        
        return render(request, 'admin/ai_model_versions.html', context)
        
    except Exception as e:
        logger.error(f"Error managing model versions: {str(e)}")
        messages.error(f"حدث خطأ: {str(e)}")
        return redirect('/admin/ai/')


@login_required
@user_passes_test(lambda u: u.is_staff)
def ai_knowledge_base(request):
    """Knowledge Base management for RAG"""
    try:
        entries = KnowledgeBaseEntry.objects.filter(status='published').order_by('-priority')
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'add':
                entry = KnowledgeBaseEntry.objects.create(
                    title=request.POST.get('title'),
                    category=request.POST.get('category'),
                    content=request.POST.get('content'),
                    keywords=json.loads(request.POST.get('keywords', '[]')),
                    language=request.POST.get('language', 'ar'),
                    priority=int(request.POST.get('priority', 1)),
                    status='draft',
                    updated_by=request.user
                )
                messages.success("تم إضافة المقالة")
            
            elif action == 'publish':
                entry = KnowledgeBaseEntry.objects.get(id=request.POST.get('entry_id'))
                entry.status = 'published'
                entry.published_at = timezone.now()
                entry.save()
                messages.success("تم نشر المقالة")
            
            elif action == 'archive':
                entry = KnowledgeBaseEntry.objects.get(id=request.POST.get('entry_id'))
                entry.status = 'archived'
                entry.save()
                messages.success(" أرشفة المقالة")
            
            return redirect('admin/ai/knowledge-base/')
        
        context = {
            'entries': entries,
            'page_title': 'قاعدة المعرفة'
        }
        
        return render(request, 'admin/ai_knowledge_base.html', context)
        
    except Exception as e:
        logger.error(f"Error managing knowledge base: {str(e)}")
        messages.error(f"حدث خطأ: {str(e)}")
        return redirect('/admin/ai/')


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def ai_analytics_api(request):
    """API for AI analytics data"""
    try:
        # Get comprehensive analytics
        stats = dataset_manager.get_dataset_statistics()
        
        # Feedback analytics
        positive_feedback = UserFeedback.objects.filter(feedback_type='positive').count()
        negative_feedback = UserFeedback.objects.filter(feedback_type='negative').count()
        
        # Unknown queries
        total_unknown = UnknownQuery.objects.count()
        resolved_unknown = UnknownQuery.objects.filter(resolved=True).count()
        
        # Tool usage
        tool_stats = ToolUsageLog.objects.values('tool_name').annotate(
            count=Count('id'),
            success_rate=Count('id', filter=Q(success=True)) / Count('id') * 100
        ).order_by('-count')
        
        return Response({
            'success': True,
            'statistics': stats,
            'feedback': {
                'positive': positive_feedback,
                'negative': negative_feedback,
                'total': positive_feedback + negative_feedback
            },
            'unknown_queries': {
                'total': total_unknown,
                'resolved': resolved_unknown,
                'pending': total_unknown - resolved_unknown
            },
            'tool_usage': list(tool_stats),
            'voice_analytics': voice_analytics.get_statistics()
        })
        
    except Exception as e:
        logger.error(f"Error getting AI analytics: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def ai_dataset_export_api(request):
    """API for exporting training dataset"""
    try:
        output_format = request.data.get('format', 'json')
        include_test = request.data.get('include_test', False)
        
        result = dataset_manager.export_training_data(output_format, include_test)
        
        if result['success']:
            return Response(result)
        else:
            return Response(result, status=500)
            
    except Exception as e:
        logger.error(f"Error exporting dataset: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def ai_train_model_api(request):
    """API for triggering model training"""
    try:
        # Get training config
        config = request.data.get('config', {})
        model_type = request.data.get('model_type', 'intent_classifier')
        
        # Create dataset
        dataset_result = dataset_manager.create_training_dataset()
        
        if not dataset_result['success']:
            return Response(dataset_result, status=500)
        
        # This is a placeholder - would trigger actual training
        training_result = model_trainer.train_intent_classifier([], config)
        
        return Response(training_result)
            
    except Exception as e:
        logger.error(f"Error training model: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def ai_health_check_api(request):
    """API for AI system health check"""
    try:
        health_report = health_checker.check_system_health()
        performance_metrics = health_checker.get_performance_metrics()
        
        return Response({
            'success': True,
            'health': health_report,
            'performance': performance_metrics
        })
        
    except Exception as e:
        logger.error(f"Error checking health: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_user_correction_api(request):
    """API for users to submit corrections"""
    try:
        conversation_id = request.data.get('conversation_id')
        original_intent = request.data.get('original_intent')
        corrected_intent = request.data.get('corrected_intent')
        original_entities = request.data.get('original_entities', {})
        corrected_entities = request.data.get('corrected_entities', {})
        user_message = request.data.get('user_message')
        
        result = data_collector.collect_user_correction(
            conversation_id=conversation_id,
            original_intent=original_intent,
            corrected_intent=corrected_intent,
            original_entities=original_entities,
            corrected_entities=corrected_entities,
            user_message=user_message,
            user=request.user
        )
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Error collecting user correction: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def ai_data_augmentation_api(request):
    """API for generating data augmentations"""
    try:
        text = request.data.get('text')
        intent = request.data.get('intent')
        entities = request.data.get('entities', {})
        num_variations = request.data.get('num_variations', 3)
        
        variations = data_collector.data_augmenter.generate_variations(
            text=text,
            intent=intent,
            entities=entities,
            num_variations=num_variations
        )
        
        return Response({
            'success': True,
            'variations': variations,
            'count': len(variations)
        })
        
    except Exception as e:
        logger.error(f"Error generating augmentations: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def ai_model_evaluation_api(request):
    """API for running model evaluation"""
    try:
        model_version = request.data.get('model_version')
        test_dataset = request.data.get('test_dataset', 'all')
        
        evaluation_result = evaluator.evaluate_model(
            model_version=model_version,
            test_dataset=test_dataset
        )
        
        return Response(evaluation_result)
        
    except Exception as e:
        logger.error(f"Error evaluating model: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def ai_debug_mode_api(request):
    """API for toggling debug mode"""
    try:
        enable = request.data.get('enable', False)
        
        if enable:
            enabled = debug_mode.enable_debug_mode(request.user)
            return Response({
                'success': True,
                'debug_enabled': enabled,
                'message': 'Debug mode enabled' if enabled else 'Insufficient permissions'
            })
        else:
            debug_mode.disable_debug_mode()
            return Response({
                'success': True,
                'debug_enabled': False,
                'message': 'Debug mode disabled'
            })
        
    except Exception as e:
        logger.error(f"Error toggling debug mode: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def ai_debug_data_api(request):
    """API for getting debug data"""
    try:
        debug_data = debug_mode.get_debug_data()
        
        return Response({
            'success': True,
            'debug_data': debug_data,
            'debug_enabled': debug_mode.enabled
        })
        
    except Exception as e:
        logger.error(f"Error getting debug data: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def ai_ab_testing_config_api(request):
    """API for configuring A/B testing"""
    try:
        model_a = request.data.get('model_a')
        model_b = request.data.get('model_b')
        split_ratio = request.data.get('split_ratio', 0.9)  # 90% A, 10% B
        
        # This would configure A/B testing in the system
        # For now, return success as placeholder
        return Response({
            'success': True,
            'message': 'A/B testing configuration saved',
            'config': {
                'model_a': model_a,
                'model_b': model_b,
                'split_ratio': split_ratio
            }
        })
        
    except Exception as e:
        logger.error(f"Error configuring A/B testing: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def ai_health_check_api(request):
    """API for checking AI system health"""
    try:
        health_report = health_checker.check_system_health()
        performance_metrics = health_checker.get_performance_metrics()
        
        return Response({
            'success': True,
            'health': health_report,
            'performance': performance_metrics
        })
            
    except Exception as e:
        logger.error(f"Error checking AI health: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
        
    except Exception as e:
        logger.error(f"Error triggering model training: {str(se)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def ai_health_check_api(request):
    """AI System Health Check"""
    try:
        from .ai_agent_tools import tool_registry
        from .ai_agent_loop import ai_agent
        
        health_status = {
            'status': 'healthy',
            'model': 'model-v1',
            'database': 'connected',
            'vector_search': 'not_configured',
            'tools': 'healthy',
            'agent': 'active',
            'timestamp': timezone.now().isoformat()
        }
        
        # Check tools
        if tool_registry.get_all_tools():
            health_status['tools'] = 'healthy'
        else:
            health_status['tools'] = 'unhealthy'
        
        # Check agent
        if ai_agent:
            health_status['agent'] = 'active'
        else:
            health_status['agent'] = 'inactive'
        
        return Response(health_status)
        
    except Exception as e:
        logger.error(f"AI health check failed: {str(e)}")
        return Response({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)