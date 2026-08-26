"""
Django Management Command to Schedule Automated Backups
أمر إدارة Django لجدولة النسخ الاحتياطي التلقائي
"""

import os
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Configure and manage scheduled database backups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--setup',
            action='store_true',
            help='Setup scheduled backup configuration',
            default=False
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show current backup schedule status',
            default=False
        )
        parser.add_argument(
            '--enable',
            action='store_true',
            help='Enable scheduled backups',
            default=False
        )
        parser.add_argument(
            '--disable',
            action='store_true',
            help='Disable scheduled backups',
            default=False
        )
        parser.add_argument(
            '--schedule',
            type=str,
            help='Backup schedule (cron format)',
            default='0 2 * * *'  # Daily at 2 AM
        )
        parser.add_argument(
            '--retention',
            type=int,
            help='Number of days to keep backups',
            default=7
        )

    def handle(self, *args, **options):
        setup = options['setup']
        status = options['status']
        enable = options['enable']
        disable = options['disable']
        schedule = options['schedule']
        retention = options['retention']

        config_file = self.get_config_file()

        if setup:
            self.setup_schedule(config_file, schedule, retention)
        elif status:
            self.show_status(config_file)
        elif enable:
            self.enable_schedule(config_file)
        elif disable:
            self.disable_schedule(config_file)
        else:
            self.show_help()

    def get_config_file(self):
        """Get path to backup configuration file"""
        config_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, 'backup_schedule.json')

    def setup_schedule(self, config_file, schedule, retention):
        """Setup backup schedule configuration"""
        config = {
            'enabled': True,
            'schedule': schedule,
            'retention_days': retention,
            'output_dir': 'backups',
            'compress': True,
            'max_backups': 10,
            'created_at': datetime.now().isoformat(),
            'last_backup': None,
            'next_backup': None
        }

        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        self.stdout.write(
            self.style.SUCCESS('Backup schedule configured successfully')
        )
        self.stdout.write(f'Schedule: {schedule}')
        self.stdout.write(f'Retention: {retention} days')
        self.stdout.write(f'Config file: {config_file}')

    def show_status(self, config_file):
        """Show current backup schedule status"""
        if not os.path.exists(config_file):
            self.stdout.write('No backup schedule configured.')
            return

        with open(config_file, 'r') as f:
            config = json.load(f)

        self.stdout.write('Backup Schedule Status:\n')
        self.stdout.write(f'Enabled: {"Yes" if config["enabled"] else "No"}')
        self.stdout.write(f'Schedule: {config["schedule"]}')
        self.stdout.write(f'Retention: {config["retention_days"]} days')
        self.stdout.write(f'Output directory: {config["output_dir"]}')
        self.stdout.write(f'Compress: {"Yes" if config["compress"] else "No"}')
        self.stdout.write(f'Max backups: {config["max_backups"]}')
        
        if config.get('last_backup'):
            self.stdout.write(f'Last backup: {config["last_backup"]}')
        else:
            self.stdout.write('Last backup: Never')
        
        if config.get('next_backup'):
            self.stdout.write(f'Next backup: {config["next_backup"]}')
        else:
            self.stdout.write('Next backup: Not scheduled')

    def enable_schedule(self, config_file):
        """Enable scheduled backups"""
        if not os.path.exists(config_file):
            self.stdout.write(
                self.style.ERROR('No backup schedule configured. Use --setup first.')
            )
            return

        with open(config_file, 'r') as f:
            config = json.load(f)

        config['enabled'] = True
        config['updated_at'] = datetime.now().isoformat()

        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        self.stdout.write(
            self.style.SUCCESS('Scheduled backups enabled')
        )

    def disable_schedule(self, config_file):
        """Disable scheduled backups"""
        if not os.path.exists(config_file):
            self.stdout.write(
                self.style.ERROR('No backup schedule configured.')
            )
            return

        with open(config_file, 'r') as f:
            config = json.load(f)

        config['enabled'] = False
        config['updated_at'] = datetime.now().isoformat()

        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        self.stdout.write(
            self.style.WARNING('Scheduled backups disabled')
        )

    def show_help(self):
        """Show help information"""
        self.stdout.write('Backup Schedule Management Commands:\n')
        self.stdout.write('--setup       Setup backup schedule')
        self.stdout.write('--status      Show current status')
        self.stdout.write('--enable      Enable scheduled backups')
        self.stdout.write('--disable     Disable scheduled backups')
        self.stdout.write('--schedule    Set backup schedule (cron format)')
        self.stdout.write('--retention   Set retention period in days')