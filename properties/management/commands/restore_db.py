"""
Django Management Command for Database Restore
أمر إدارة Django لاستعادة قاعدة البيانات
"""

import os
import shutil
import gzip
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess


class Command(BaseCommand):
    help = 'Restore database from a backup file'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Path to the backup file'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt',
            default=False
        )

    def handle(self, *args, **options):
        backup_file = options['backup_file']
        confirm = options['confirm']

        if not os.path.exists(backup_file):
            self.stdout.write(
                self.style.ERROR(f'Backup file not found: {backup_file}')
            )
            return

        # Get database engine
        db_engine = settings.DATABASES['default']['ENGINE']

        if not confirm:
            self.stdout.write(
                self.style.WARNING('⚠️  This will overwrite the current database!')
            )
            response = input('Are you sure you want to continue? (yes/no): ')
            if response.lower() != 'yes':
                self.stdout.write('Restore cancelled.')
                return

        try:
            if 'sqlite' in db_engine:
                self.restore_sqlite(backup_file)
            elif 'postgresql' in db_engine:
                self.restore_postgresql(backup_file)
            elif 'mysql' in db_engine:
                self.restore_mysql(backup_file)
            else:
                self.stdout.write(
                    self.style.ERROR(f'Unsupported database engine: {db_engine}')
                )
                return

            self.stdout.write(
                self.style.SUCCESS('Database restored successfully!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Restore failed: {str(e)}')
            )
            raise

    def restore_sqlite(self, backup_file):
        """Restore SQLite database"""
        db_path = settings.DATABASES['default']['NAME']
        
        # Handle compressed files
        if backup_file.endswith('.gz'):
            temp_file = backup_file[:-3]
            with gzip.open(backup_file, 'rb') as f_in:
                with open(temp_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            backup_file = temp_file
        
        # Backup current database
        if os.path.exists(db_path):
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            shutil.copy2(db_path, f'{db_path}.backup_{timestamp}')
            self.stdout.write(f'Current database backed up to: {db_path}.backup_{timestamp}')
        
        # Restore from backup
        shutil.copy2(backup_file, db_path)
        
        # Clean up temp file if it was compressed
        if backup_file.endswith('.temp'):
            os.remove(backup_file)
        
        self.stdout.write(f'SQLite database restored from: {backup_file}')

    def restore_postgresql(self, backup_file):
        """Restore PostgreSQL database"""
        db_config = settings.DATABASES['default']
        
        # Handle compressed files
        if backup_file.endswith('.gz'):
            temp_file = backup_file[:-3]
            with gzip.open(backup_file, 'rb') as f_in:
                with open(temp_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            backup_file = temp_file
        
        # Build pg_restore command
        pg_restore_cmd = [
            'pg_restore',
            f'--host={db_config["HOST"]}',
            f'--port={db_config["PORT"]}',
            f'--username={db_config["USER"]}',
            f'--dbname={db_config["NAME"]}',
            '--no-password',
            '--clean',
            '--if-exists',
            backup_file
        ]
        
        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['PASSWORD']
        
        # Execute restore
        subprocess.run(pg_restore_cmd, env=env, check=True)
        
        # Clean up temp file if it was compressed
        if backup_file.endswith('.temp'):
            os.remove(backup_file)
        
        self.stdout.write(f'PostgreSQL database restored from: {backup_file}')

    def restore_mysql(self, backup_file):
        """Restore MySQL database"""
        db_config = settings.DATABASES['default']
        
        # Handle compressed files
        if backup_file.endswith('.gz'):
            temp_file = backup_file[:-3]
            with gzip.open(backup_file, 'rb') as f_in:
                with open(temp_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            backup_file = temp_file
        
        # Build mysql command
        mysql_cmd = [
            'mysql',
            f'--host={db_config["HOST"]}',
            f'--port={db_config["PORT"]}',
            f'--user={db_config["USER"]}',
            f'--password={db_config["PASSWORD"]}',
            db_config['NAME']
        ]
        
        # Execute restore
        with open(backup_file, 'r') as sql_file:
            subprocess.run(mysql_cmd, stdin=sql_file, check=True)
        
        # Clean up temp file if it was compressed
        if backup_file.endswith('.temp'):
            os.remove(backup_file)
        
        self.stdout.write(f'MySQL database restored from: {backup_file}')