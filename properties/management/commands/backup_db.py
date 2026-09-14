"""
Django Management Command for Database Backup
أمر إدارة Django للنسخ الاحتياطي لقاعدة البيانات
"""

import os
import shutil
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
import subprocess


class Command(BaseCommand):
    help = 'Create a backup of the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Output directory for backup files',
            default='backups'
        )
        parser.add_argument(
            '--name',
            type=str,
            help='Custom name for the backup file',
            default=None
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            help='Compress the backup file',
            default=True
        )

    def handle(self, *args, **options):
        output_dir = options['output']
        custom_name = options['name']
        compress = options['compress']

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Generate backup filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if custom_name:
            filename = f"{custom_name}_{timestamp}"
        else:
            filename = f"backup_{timestamp}"

        # Get database engine
        db_engine = settings.DATABASES['default']['ENGINE']

        try:
            if 'sqlite' in db_engine:
                self.backup_sqlite(output_dir, filename, compress)
            elif 'postgresql' in db_engine:
                self.backup_postgresql(output_dir, filename, compress)
            elif 'mysql' in db_engine:
                self.backup_mysql(output_dir, filename, compress)
            else:
                self.stdout.write(
                    self.style.ERROR(f'Unsupported database engine: {db_engine}')
                )
                return

            self.stdout.write(
                self.style.SUCCESS(f'Backup created successfully: {filename}')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Backup failed: {str(e)}')
            )
            raise

    def backup_sqlite(self, output_dir, filename, compress):
        """Backup SQLite database"""
        db_path = settings.DATABASES['default']['NAME']
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f'Database file not found: {db_path}')

        backup_path = os.path.join(output_dir, f'{filename}.db')
        
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        if compress:
            self.compress_file(backup_path)
            backup_path += '.gz'
        
        self.stdout.write(f'SQLite backup: {backup_path}')

    def backup_postgresql(self, output_dir, filename, compress):
        """Backup PostgreSQL database"""
        db_config = settings.DATABASES['default']
        
        # Build pg_dump command
        pg_dump_cmd = [
            'pg_dump',
            f'--host={db_config["HOST"]}',
            f'--port={db_config["PORT"]}',
            f'--username={db_config["USER"]}',
            f'--dbname={db_config["NAME"]}',
            '--no-password',
            '--format=custom',
            f'--file={os.path.join(output_dir, f"{filename}.dump")}'
        ]
        
        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['PASSWORD']
        
        # Execute backup
        subprocess.run(pg_dump_cmd, env=env, check=True)
        
        if compress:
            self.compress_file(os.path.join(output_dir, f"{filename}.dump"))
        
        self.stdout.write(f'PostgreSQL backup: {filename}.dump')

    def backup_mysql(self, output_dir, filename, compress):
        """Backup MySQL database"""
        db_config = settings.DATABASES['default']
        
        # Build mysqldump command
        mysqldump_cmd = [
            'mysqldump',
            f'--host={db_config["HOST"]}',
            f'--port={db_config["PORT"]}',
            f'--user={db_config["USER"]}',
            f'--password={db_config["PASSWORD"]}',
            db_config['NAME'],
            f'--result-file={os.path.join(output_dir, f"{filename}.sql")}'
        ]
        
        # Execute backup
        subprocess.run(mysqldump_cmd, check=True)
        
        if compress:
            self.compress_file(os.path.join(output_dir, f"{filename}.sql"))
        
        self.stdout.write(f'MySQL backup: {filename}.sql')

    def compress_file(self, filepath):
        """Compress file using gzip"""
        import gzip
        import shutil as sh
        
        with open(filepath, 'rb') as f_in:
            with gzip.open(f'{filepath}.gz', 'wb') as f_out:
                sh.copyfileobj(f_in, f_out)
        
        # Remove original file
        os.remove(filepath)
        self.stdout.write(f'Compressed: {filepath}.gz')