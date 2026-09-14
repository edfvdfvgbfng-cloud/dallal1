from django.core.management.base import BaseCommand
from properties.models import Role


class Command(BaseCommand):
    help = 'Add job-related permissions to existing roles'

    def handle(self, *args, **options):
        # Job-related permissions
        job_permissions = [
            'can_post_job',
            'can_edit_any_job',
            'can_delete_any_job',
            'can_manage_job_applications',
        ]
        
        # Get all roles
        roles = Role.objects.all()
        
        updated_count = 0
        
        for role in roles:
            role_permissions = role.permissions.split(',') if role.permissions else []
            
            for permission in job_permissions:
                if permission not in role_permissions:
                    role_permissions.append(permission)
            
            role.permissions = ','.join(role_permissions)
            role.save()
            updated_count += 1
            print(f'Updated permissions for role: {role.name_en}')
        
        print(f'Successfully updated {updated_count} roles with job permissions')