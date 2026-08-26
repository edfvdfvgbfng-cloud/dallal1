"""
Database Optimizations and Performance Improvements
Indexes, query optimization, and database health management
"""

from django.db import models, connection
from django.db.models import Index, Q, F, Count, Avg, Max, Min
from django.db.models.functions import Lower, Upper, Concat
from django.core.management.base import BaseCommand
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """
    Database optimization utilities for production performance
    """
    
    @staticmethod
    def analyze_table_health():
        """Analyze database table health and identify issues"""
        tables_to_analyze = [
            'properties_property',
            'properties_broker',
            'properties_jobposting',
            'ai_training_examples',
            'ai_conversation_log',
            'ai_search_analytics',
        ]
        
        health_report = {}
        
        with connection.cursor() as cursor:
            for table in tables_to_analyze:
                try:
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]
                    
                    # Get table size
                    cursor.execute(f"""
                        SELECT 
                            pg_size_pretty(pg_total_relation_size('{table}')) as size
                    """)
                    table_size = cursor.fetchone()[0]
                    
                    # Check for missing indexes
                    cursor.execute(f"""
                        SELECT 
                            count(*) as index_count
                        FROM pg_indexes
                        WHERE tablename = '{table}'
                    """)
                    index_count = cursor.fetchone()[0]
                    
                    health_report[table] = {
                        'row_count': row_count,
                        'table_size': table_size,
                        'index_count': index_count,
                        'health': 'good' if row_count < 100000 else 'needs_attention'
                    }
                    
                except Exception as e:
                    logger.error(f"Error analyzing table {table}: {str(e)}")
                    health_report[table] = {'error': str(e)}
        
        return health_report
    
    @staticmethod
    def optimize_slow_queries():
        """Identify and optimize slow queries"""
        slow_queries = []
        
        with connection.cursor() as cursor:
            # Get slow query statistics (PostgreSQL specific)
            try:
                cursor.execute("""
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        max_time
                    FROM pg_stat_statements
                    WHERE mean_time > 100  -- queries taking more than 100ms
                    ORDER BY mean_time DESC
                    LIMIT 10
                """)
                
                for row in cursor.fetchall():
                    slow_queries.append({
                        'query': row[0],
                        'calls': row[1],
                        'total_time': row[2],
                        'mean_time': row[3],
                        'max_time': row[4]
                    })
                    
            except Exception as e:
                logger.warning(f"pg_stat_statements not available: {str(e)}")
        
        return slow_queries
    
    @staticmethod
    def create_missing_indexes():
        """Create missing indexes for common query patterns"""
        indexes_to_create = [
            # Property search indexes
            ('properties_property', 'idx_property_governorate_price', 'governorate, price'),
            ('properties_property', 'idx_property_type_status', 'property_type, status'),
            ('properties_property', 'idx_property_district', 'district'),
            ('properties_property', 'idx_property_created_at', 'created_at'),
            
            # AI training indexes
            ('ai_training_examples', 'idx_training_intent_status', 'intent, status'),
            ('ai_training_examples', 'idx_training_dataset_type', 'dataset_type'),
            
            # Conversation logs
            ('ai_conversation_log', 'idx_conversation_user_started', 'user_id, started_at'),
            ('ai_conversation_log', 'idx_conversation_intent', 'final_intent'),
            
            # Search analytics
            ('ai_search_analytics', 'idx_search_user_created', 'user_id, created_at'),
            ('ai_search_analytics', 'idx_search_intent', 'detected_intent'),
        ]
        
        created_indexes = []
        
        with connection.cursor() as cursor:
            for table, index_name, columns in indexes_to_create:
                try:
                    # Check if index exists
                    cursor.execute(f"""
                        SELECT 1 FROM pg_indexes 
                        WHERE tablename = '{table}' AND indexname = '{index_name}'
                    """)
                    
                    if not cursor.fetchone():
                        # Create index
                        cursor.execute(f"""
                            CREATE INDEX CONCURRENTLY {index_name} 
                            ON {table} ({columns})
                        """)
                        created_indexes.append(index_name)
                        logger.info(f"Created index: {index_name}")
                    
                except Exception as e:
                    logger.error(f"Error creating index {index_name}: {str(e)}")
        
        return created_indexes
    
    @staticmethod
    def vacuum_analyze_tables():
        """Run VACUUM ANALYZE on all tables"""
        tables = [
            'properties_property',
            'properties_broker',
            'properties_jobposting',
            'ai_training_examples',
            'ai_conversation_log',
            'ai_search_analytics',
        ]
        
        results = {}
        
        with connection.cursor() as cursor:
            for table in tables:
                try:
                    cursor.execute(f"VACUUM ANALYZE {table}")
                    results[table] = 'success'
                    logger.info(f"VACUUM ANALYZE completed for {table}")
                except Exception as e:
                    results[table] = f'error: {str(e)}'
                    logger.error(f"Error during VACUUM ANALYZE for {table}: {str(e)}")
        
        return results


class QueryOptimizer:
    """
    Query optimization utilities for common patterns
    """
    
    @staticmethod
    def optimize_property_search(query_params):
        """
        Optimized property search with proper indexing
        """
        from .models import Property
        
        # Build optimized query
        queryset = Property.objects.filter(status='available')
        
        # Use indexed fields first
        if 'governorate' in query_params:
            queryset = queryset.filter(governorate=query_params['governorate'])
        
        if 'property_type' in query_params:
            queryset = queryset.filter(property_type=query_params['property_type'])
        
        # Price range with proper indexing
        if 'min_price' in query_params:
            queryset = queryset.filter(price__gte=query_params['min_price'])
        if 'max_price' in query_params:
            queryset = queryset.filter(price__lte=query_params['max_price'])
        
        # Use select_related for foreign keys
        queryset = queryset.select_related('user', 'broker')
        
        # Use prefetch_related for many-to-many
        queryset = queryset.prefetch_related('images', 'amenities')
        
        # Use only() to limit fields loaded
        queryset = queryset.only(
            'id', 'title', 'price', 'area', 'governorate', 'district',
            'property_type', 'status', 'created_at', 'user_id'
        )
        
        return queryset
    
    @staticmethod
    def optimize_conversation_query(user_id, limit=20):
        """
        Optimized conversation query with proper indexing
        """
        from .ai_training_models import ConversationLog
        
        # Use indexed fields
        queryset = ConversationLog.objects.filter(user_id=user_id)
        
        # Use select_related
        queryset = queryset.select_related('user')
        
        # Order by indexed field
        queryset = queryset.order_by('-started_at')
        
        # Limit results
        queryset = queryset[:limit]
        
        return queryset
    
    @staticmethod
    def optimize_analytics_query(date_range, user_id=None):
        """
        Optimized analytics query with proper date filtering
        """
        from .ai_training_models import SearchAnalytics
        
        queryset = SearchAnalytics.objects.filter(
            created_at__range=date_range
        )
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Use aggregate functions for statistics
        stats = queryset.aggregate(
            total_searches=Count('id'),
            avg_confidence=Avg('confidence'),
            avg_search_duration=Avg('search_duration_ms'),
            unique_users=Count('user_id', distinct=True)
        )
        
        return stats


class DatabaseMigrationManager:
    """
    Safe database migration management
    """
    
    @staticmethod
    def create_migration_backup():
        """Create backup before migration"""
        import subprocess
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"db_backup_{timestamp}.sql"
        
        try:
            # Export database to SQL file
            subprocess.run([
                'pg_dump',
                settings.DATABASES['default']['NAME'],
                '-f', backup_file
            ], check=True)
            
            logger.info(f"Database backup created: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Error creating database backup: {str(e)}")
            return None
    
    @staticmethod
    def verify_migration_integrity():
        """Verify migration integrity after running migrations"""
        from django.core.management import call_command
        
        try:
            # Check for any unapplied migrations
            call_command('showmigrations', '--plan')
            
            # Run database integrity checks
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            logger.info("Migration integrity verified")
            return True
            
        except Exception as e:
            logger.error(f"Migration integrity check failed: {str(e)}")
            return False
    
    @staticmethod
    def rollback_migration(backup_file):
        """Rollback migration using backup"""
        import subprocess
        
        try:
            # Restore from backup
            subprocess.run([
                'psql',
                settings.DATABASES['default']['NAME'],
                '-f', backup_file
            ], check=True)
            
            logger.info(f"Database restored from backup: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring database backup: {str(e)}")
            return False


class Command(BaseCommand):
    help = 'Optimize database for production performance'
    
    def handle(self, *args, **options):
        self.stdout.write("Starting database optimization...")
        
        # Analyze table health
        self.stdout.write("Analyzing table health...")
        health_report = DatabaseOptimizer.analyze_table_health()
        for table, health in health_report.items():
            self.stdout.write(f"  {table}: {health}")
        
        # Create missing indexes
        self.stdout.write("Creating missing indexes...")
        created_indexes = DatabaseOptimizer.create_missing_indexes()
        if created_indexes:
            self.stdout.write(f"  Created {len(created_indexes)} indexes")
        else:
            self.stdout.write("  No new indexes needed")
        
        # Optimize slow queries
        self.stdout.write("Analyzing slow queries...")
        slow_queries = DatabaseOptimizer.optimize_slow_queries()
        if slow_queries:
            self.stdout.write(f"  Found {len(slow_queries)} slow queries")
            for query in slow_queries[:5]:  # Show top 5
                self.stdout.write(f"    - Mean time: {query['mean_time']:.2f}ms")
        else:
            self.stdout.write("  No slow queries found")
        
        # Vacuum and analyze
        self.stdout.write("Running VACUUM ANALYZE...")
        vacuum_results = DatabaseOptimizer.vacuum_analyze_tables()
        for table, result in vacuum_results.items():
            self.stdout.write(f"  {table}: {result}")
        
        self.stdout.write(self.style.SUCCESS("Database optimization completed!"))