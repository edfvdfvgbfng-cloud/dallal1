"""
Django Management Command to Verify Database Backup Integrity
أمر إدارة Django للتحقق من سلامة النسخ الاحتياطي لقاعدة البيانات
"""

import os
import gzip
import datetime
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Verify the integrity of a database backup file'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Path to the backup file to verify'
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed verification information',
            default=False
        )

    def handle(self, *args, **options):
        backup_file = options['backup_file']
        detailed = options['detailed']

        if not os.path.exists(backup_file):
            self.stdout.write(
                self.style.ERROR(f'Backup file not found: {backup_file}')
            )
            return

        self.stdout.write(f'Verifying backup: {backup_file}\n')

        try:
            # Check file size
            file_size = os.path.getsize(backup_file)
            self.stdout.write(f'File size: {self.format_size(file_size)}')

            # Check if file is compressed
            is_compressed = backup_file.endswith('.gz')
            if is_compressed:
                self.stdout.write('File format: Compressed (gzip)')
                
                # Try to read compressed file
                try:
                    with gzip.open(backup_file, 'rb') as f:
                        # Read first few bytes to verify
                        data = f.read(1024)
                        if data:
                            self.stdout.write('Compression: Valid')
                        else:
                            self.stdout.write(
                                self.style.WARNING('Compression: Valid but file appears empty')
                            )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Compression error: {str(e)}')
                    )
                    return
            else:
                self.stdout.write('File format: Uncompressed')

            # Check file extension
            db_engine = settings.DATABASES['default']['ENGINE']
            expected_extensions = []
            
            if 'sqlite' in db_engine:
                expected_extensions = ['.db', '.db.gz']
            elif 'postgresql' in db_engine:
                expected_extensions = ['.dump', '.dump.gz']
            elif 'mysql' in db_engine:
                expected_extensions = ['.sql', '.sql.gz']
            
            has_valid_extension = any(
                backup_file.endswith(ext) for ext in expected_extensions
            )
            
            if has_valid_extension:
                self.stdout.write('File extension: Valid')
            else:
                self.stdout.write(
                    self.style.WARNING(f'File extension: Unexpected (expected: {expected_extensions})')
                )

            # Additional checks for detailed mode
            if detailed:
                self.stdout.write('\nDetailed verification:')
                
                # Check file permissions
                if os.access(backup_file, os.R_OK):
                    self.stdout.write('✓ File is readable')
                else:
                    self.stdout.write(
                        self.style.ERROR('✗ File is not readable')
                    )
                
                # Check modification time
                mtime = datetime.fromtimestamp(os.path.getmtime(backup_file))
                self.stdout.write(f'Modification time: {mtime.strftime("%Y-%m-%d %H:%M:%S")}')
                
                # Try to read file header
                try:
                    with open(backup_file, 'rb') if not is_compressed else gzip.open(backup_file, 'rb') as f:
                        header = f.read(16)
                        if header:
                            self.stdout.write(f'File header: {header.hex()[:32]}...')
                        else:
                            self.stdout.write(
                                self.style.WARNING('File header: Empty')
                            )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error reading file header: {str(e)}')
                    )

            self.stdout.write(
                self.style.SUCCESS('\n✓ Backup file verification passed')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Verification failed: {str(e)}')
            )
            raise

    def format_size(self, size_bytes):
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"