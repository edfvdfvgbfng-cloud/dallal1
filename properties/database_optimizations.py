"""
Database optimization utilities and indexes for improved performance.
"""

from django.db import connection, models
from django.db.models import Index, Func
from django.db.models.functions import Lower


class TrigramSimilarity(Func):
    """Custom function for trigram similarity in PostgreSQL"""
    function = 'similarity'
    output_field = models.FloatField()


def optimize_database():
    """Apply database optimizations and indexes"""
    
    optimizations = [
        # Property indexes
        'CREATE INDEX IF NOT EXISTS idx_property_status_type ON properties_property(status, type);',
        'CREATE INDEX IF NOT EXISTS idx_property_price ON properties_property(price);',
        'CREATE INDEX IF NOT EXISTS idx_property_area ON properties_property(area);',
        'CREATE INDEX IF NOT EXISTS idx_property_created_at ON properties_property(created_at DESC);',
        'CREATE INDEX IF NOT EXISTS idx_property_featured ON properties_property(is_featured, is_promoted);',
        'CREATE INDEX IF NOT EXISTS idx_property_location ON properties_property(governorate, district);',
        
        # Full-text search index (PostgreSQL specific)
        'CREATE INDEX IF NOT EXISTS idx_property_search ON properties_property USING GIN(to_tsvector("arabic", title || \' \' || description));',
        
        # User indexes
        'CREATE INDEX IF NOT EXISTS idx_user_email ON auth_user(email);',
        'CREATE INDEX IF NOT EXISTS idx_user_username ON auth_user(username);',
        
        # Broker indexes
        'CREATE INDEX IF NOT EXISTS idx_broker_active ON properties_broker(is_active, is_verified);',
        'CREATE INDEX IF NOT EXISTS idx_broker_governorate ON properties_broker(governorate);',
        
        # Message indexes
        'CREATE INDEX IF NOT EXISTS idx_message_created ON properties_message(created_at DESC);',
        'CREATE INDEX IF NOT EXISTS idx_message_property ON properties_message(property_id);',
        
        # Conversation indexes
        'CREATE INDEX IF NOT EXISTS idx_conversation_active ON properties_conversation(is_active, last_message_at DESC);',
        
        # Chat message indexes
        'CREATE INDEX IF NOT EXISTS idx_chat_message_conversation ON properties_chatmessage(conversation_id, created_at DESC);',
        
        # Notification indexes
        'CREATE INDEX IF NOT EXISTS idx_notification_user_read ON properties_notification(user_id, is_read, created_at DESC);',
        
        # Compound indexes for common queries
        'CREATE INDEX IF NOT EXISTS idx_property_search_filters ON properties_property(status, type, governorate, price, area);',
        'CREATE INDEX IF NOT EXISTS idx_property_broker_status ON properties_property(broker_id, status, is_active);',
    ]
    
    with connection.cursor() as cursor:
        for sql in optimizations:
            try:
                cursor.execute(sql)
            except Exception as e:
                print(f"Warning: Could not execute {sql}: {e}")


def analyze_tables():
    """Analyze database tables for query optimization"""
    
    tables = [
        'properties_property',
        'properties_broker',
        'properties_message',
        'properties_conversation',
        'properties_chatmessage',
        'properties_notification',
    ]
    
    with connection.cursor() as cursor:
        for table in tables:
            try:
                cursor.execute(f"ANALYZE {table};")
            except Exception as e:
                print(f"Warning: Could not analyze {table}: {e}")


def vacuum_tables():
    """Vacuum database tables to reclaim storage"""
    
    tables = [
        'properties_property',
        'properties_message',
        'properties_chatmessage',
    ]
    
    with connection.cursor() as cursor:
        for table in tables:
            try:
                cursor.execute(f"VACUUM ANALYZE {table};")
            except Exception as e:
                print(f"Warning: Could not vacuum {table}: {e}")


def get_query_stats():
    """Get database query statistics"""
    
    stats = {}
    
    with connection.cursor() as cursor:
        # Table sizes
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
        """)
        stats['table_sizes'] = cursor.fetchall()
        
        # Index usage
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan as index_scans,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched
            FROM pg_stat_user_indexes
            ORDER BY idx_scan DESC;
        """)
        stats['index_usage'] = cursor.fetchall()
        
        # Sequential scans
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                seq_scan as sequential_scans,
                idx_scan as index_scans,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes
            FROM pg_stat_user_tables
            ORDER BY seq_scan DESC;
        """)
        stats['table_stats'] = cursor.fetchall()
    
    return stats


def optimize_query_sets():
    """Recommend query set optimizations based on statistics"""
    
    recommendations = []
    
    stats = get_query_stats()
    
    # Check for high sequential scans
    for table_stat in stats['table_stats']:
        if table_stat[2] > 1000:  # High sequential scans
            recommendations.append({
                'table': table_stat[1],
                'issue': 'High sequential scans',
                'recommendation': 'Consider adding indexes for frequently queried columns'
            })
    
    # Check for unused indexes
    for index_stat in stats['index_usage']:
        if index_stat[3] == 0:  # No index scans
            recommendations.append({
                'index': index_stat[2],
                'issue': 'Unused index',
                'recommendation': 'Consider removing this index to save space'
            })
    
    return recommendations


class QueryOptimizer:
    """Helper class for optimizing specific queries"""
    
    @staticmethod
    def optimize_property_search(queryset, filters):
        """Optimize property search queries"""
        
        # Always use select_related and prefetch_related
        queryset = queryset.select_related('broker', 'owner').prefetch_related('images')
        
        # Apply filters efficiently
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        
        if filters.get('type'):
            queryset = queryset.filter(type=filters['type'])
        
        if filters.get('governorate'):
            queryset = queryset.filter(governorate=filters['governorate'])
        
        if filters.get('price_min'):
            queryset = queryset.filter(price__gte=filters['price_min'])
        
        if filters.get('price_max'):
            queryset = queryset.filter(price__lte=filters['price_max'])
        
        # Use only() to limit fields for list views
        if not filters.get('detail_view'):
            queryset = queryset.only(
                'id', 'title', 'slug', 'type', 'status', 'price', 'area',
                'district', 'location', 'bedrooms', 'bathrooms', 'is_featured',
                'is_promoted', 'created_at', 'broker_id'
            )
        
        return queryset
    
    @staticmethod
    def optimize_broker_queryset(queryset):
        """Optimize broker queries"""
        
        return queryset.select_related('user').prefetch_related('properties').only(
            'id', 'office_name', 'phone', 'governorate', 'is_verified',
            'is_active', 'subscription_plan', 'subscription_expires_at',
            'user__username', 'user__email'
        )
    
    @staticmethod
    def optimize_message_queryset(queryset):
        """Optimize message queries"""
        
        return queryset.select_related('sender', 'recipient', 'property').prefetch_related(
            'attachments'
        ).only(
            'id', 'subject', 'content', 'created_at', 'is_read',
            'sender_id', 'recipient_id', 'property_id'
        )
    
    @staticmethod
    def get_related_properties(property_obj, limit=4):
        """Optimized related properties query"""
        
        from .models import Property
        
        return Property.objects.filter(
            status=property_obj.status,
            type=property_obj.type
        ).exclude(
            id=property_obj.id
        ).select_related(
            'broker'
        ).prefetch_related(
            'images'
        ).only(
            'id', 'title', 'slug', 'price', 'area', 'district',
            'location', 'broker_id', 'created_at'
        )[:limit]


def create_materialized_views():
    """Create materialized views for complex queries"""
    
    views = [
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_property_stats AS
        SELECT 
            p.id,
            p.title,
            p.price,
            p.area,
            p.status,
            p.type,
            p.governorate,
            p.district,
            p.views_count,
            p.created_at,
            p.is_featured,
            p.is_promoted,
            b.id as broker_id,
            b.office_name,
            COUNT(pi.id) as image_count,
            COUNT(c.id) as comment_count,
            COUNT(l.id) as like_count
        FROM properties_property p
        LEFT JOIN properties_broker b ON p.broker_id = b.id
        LEFT JOIN properties_propertyimage pi ON p.id = pi.property_id
        LEFT JOIN properties_propertycomment c ON p.id = c.property_id
        LEFT JOIN properties_propertylike l ON p.id = l.property_id
        GROUP BY p.id, b.id
        WITH DATA;
        """,
        
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_broker_stats AS
        SELECT 
            b.id,
            b.office_name,
            b.phone,
            b.governorate,
            b.is_verified,
            b.is_active,
            COUNT(p.id) as property_count,
            SUM(CASE WHEN p.status = 'ready' THEN 1 ELSE 0 END) as active_properties,
            AVG(p.price) as avg_price,
            SUM(p.views_count) as total_views
        FROM properties_broker b
        LEFT JOIN properties_property p ON b.id = p.broker_id
        GROUP BY b.id
        WITH DATA;
        """,
    ]
    
    with connection.cursor() as cursor:
        for view_sql in views:
            try:
                cursor.execute(view_sql)
            except Exception as e:
                print(f"Warning: Could not create materialized view: {e}")


def refresh_materialized_views():
    """Refresh materialized views"""
    
    views = ['mv_property_stats', 'mv_broker_stats']
    
    with connection.cursor() as cursor:
        for view in views:
            try:
                cursor.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view};")
            except Exception as e:
                print(f"Warning: Could not refresh {view}: {e}")


def setup_database_optimizations():
    """Setup all database optimizations"""
    
    print("Setting up database optimizations...")
    
    # Create indexes
    print("Creating indexes...")
    optimize_database()
    
    # Analyze tables
    print("Analyzing tables...")
    analyze_tables()
    
    # Create materialized views
    print("Creating materialized views...")
    create_materialized_views()
    
    # Get optimization recommendations
    print("Analyzing query patterns...")
    recommendations = optimize_query_sets()
    
    if recommendations:
        print("Optimization recommendations:")
        for rec in recommendations:
            print(f"  - {rec}")
    
    print("Database optimization complete!")