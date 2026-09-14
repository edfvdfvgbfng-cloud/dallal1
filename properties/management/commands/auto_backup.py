"""
Django Management Command for Automatic Database Backup
أمر إدارة Django للنسخ الاحتياطي التلقائي لقاعدة البيانات
"""

import os
import shutil
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Automatic database backup with retention policy'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Output directory for backup files',
            default='backups'
        )
        parser.add_argument(
            '--retention-days',
            type=int,
            help='Number of days to keep backups',
            default=7
        )
        parser.add_argument(
            '--max-backups',
            type=int,
            help='Maximum number of backups to keep',
            default=10
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            help='Compress backup files',
            default=True
        )

    def handle(self, *args, **options):
        output_dir = options['output']
        retention_days = options['retention_days']
        max_backups = options['max_backups']
        compress = options['compress']

        self.stdout.write('Starting automatic database backup...')

        try:
            # Create backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f'auto_backup_{timestamp}'
            
            call_command('backup_db', 
                        output=output_dir, 
                        name=backup_name,
                        compress=compress)
            
            self.stdout.write(
                self.style.SUCCESS(f'Automatic backup created: {backup_name}')
            )

            # Clean old backups
            self.clean_old_backups(output_dir, retention_days, max_backups)

            self.stdout.write(
                self.style.SUCCESS('Automatic backup completed successfully')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Automatic backup failed: {str(e)}')
            )
            raise

    def clean_old_backups(self, output_dir, retention_days, max_backups):
        """Clean old backups based on retention policy"""
        if not os.path.exists(output_dir):
            return

        # Get all backup files
        backup_files = []
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        for filename in os.listdir(output_dir):
            filepath = os.path.join(output_dir, filename)
            
            # Skip directories
            if os.path.isdir(filepath):
                continue
            
            # Check if it's a backup file
            if any(ext in filename for ext in ['.db', '.sql', '.dump', '.gz']):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                backup_files.append((filepath, file_mtime))

        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x[1], reverse=True)

        # Remove files older than retention period
        removed_count = 0
        for filepath, file_mtime in backup_files:
            if file_mtime < cutoff_date:
                os.remove(filepath)
                self.stdout.write(f'Removed old backup: {os.path.basename(filepath)}')
                removed_count += 1

        # If we still have too many backups, remove the oldest ones
        if len(backup_files) > max_backups:
            files_to_remove = backup_files[max_backups:]
            for filepath, _ in files_to_remove:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    self.stdout.write(f'Removed excess backup: {os.path.basename(filepath)}')
                    removed_count += 1

        if removed_count > 0:
            self.stdout.write(
                self.style.WARNING(f'Cleaned {removed_count} old backup(s)')
            )
        else:
            self.stdout.write('No old backups to clean')