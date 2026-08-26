"""
Django Management Command to List Database Backups
أمر إدارة Django لعرض النسخ الاحتياطية لقاعدة البيانات
"""

import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'List all available database backups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Output directory for backup files',
            default='backups'
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed information about backups',
            default=False
        )

    def handle(self, *args, **options):
        output_dir = options['output']
        detailed = options['detailed']

        if not os.path.exists(output_dir):
            self.stdout.write(
                self.style.WARNING(f'Backup directory not found: {output_dir}')
            )
            return

        backup_files = []
        
        for filename in os.listdir(output_dir):
            filepath = os.path.join(output_dir, filename)
            
            # Skip directories
            if os.path.isdir(filepath):
                continue
            
            # Check if it's a backup file
            if any(ext in filename for ext in ['.db', '.sql', '.dump', '.gz']):
                file_size = os.path.getsize(filepath)
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                backup_files.append({
                    'name': filename,
                    'path': filepath,
                    'size': file_size,
                    'modified': file_mtime
                })

        if not backup_files:
            self.stdout.write('No backup files found.')
            return

        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x['modified'], reverse=True)

        # Display backups
        self.stdout.write(f'\nFound {len(backup_files)} backup file(s):\n')
        
        for i, backup in enumerate(backup_files, 1):
            if detailed:
                self.stdout.write(
                    f'{i}. {backup["name"]}\n'
                    f'   Size: {self.format_size(backup["size"])}\n'
                    f'   Modified: {backup["modified"].strftime("%Y-%m-%d %H:%M:%S")}\n'
                    f'   Path: {backup["path"]}\n'
                )
            else:
                self.stdout.write(
                    f'{i}. {backup["name"]} '
                    f'({self.format_size(backup["size"])}, '
                    f'{backup["modified"].strftime("%Y-%m-%d %H:%M")})'
                )

        # Calculate total size
        total_size = sum(backup['size'] for backup in backup_files)
        self.stdout.write(f'\nTotal size: {self.format_size(total_size)}')

    def format_size(self, size_bytes):
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"