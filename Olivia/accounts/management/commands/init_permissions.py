"""
Management command to initialize organizational levels and permissions.
Run with: python manage.py init_permissions
"""
from django.core.management.base import BaseCommand
from accounts.models import OrganizationalLevel, Permission, RolePermission


class Command(BaseCommand):
    help = 'Initialize organizational levels and permissions'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting permission initialization...'))

        # Create organizational levels
        levels_data = [
            {'name': 'Chief Executive Officer', 'level': 1, 'description': 'C-Level Executive'},
            {'name': 'Chief Financial Officer', 'level': 1, 'description': 'C-Level Executive'},
            {'name': 'Director', 'level': 2, 'description': 'Department Director'},
            {'name': 'Manager', 'level': 3, 'description': 'Department Manager'},
            {'name': 'Supervisor', 'level': 4, 'description': 'Team Supervisor'},
            {'name': 'Team Lead', 'level': 5, 'description': 'Team Lead'},
            {'name': 'Staff', 'level': 6, 'description': 'General Staff'},
            {'name': 'Intern', 'level': 7, 'description': 'Intern/Trainee'},
        ]

        org_levels = {}
        for level_data in levels_data:
            obj, created = OrganizationalLevel.objects.get_or_create(
                name=level_data['name'],
                defaults={'level': level_data['level'], 'description': level_data['description']}
            )
            org_levels[level_data['name']] = obj
            if created:
                self.stdout.write(f'  ✓ Created level: {level_data["name"]}')
            else:
                self.stdout.write(f'  • Level already exists: {level_data["name"]}')

        # Create permissions for each app and feature
        permissions_data = [
            # HumanResource
            ('humanresource', 'staff', 'view'),
            ('humanresource', 'staff', 'create'),
            ('humanresource', 'staff', 'edit'),
            ('humanresource', 'staff', 'delete'),
            ('humanresource', 'staff', 'export'),
            ('humanresource', 'staff', 'import'),
            ('humanresource', 'petty_cash', 'view'),
            ('humanresource', 'petty_cash', 'create'),
            ('humanresource', 'petty_cash', 'edit'),
            ('humanresource', 'petty_cash', 'delete'),
            ('humanresource', 'petty_cash', 'approve'),
            ('humanresource', 'petty_cash', 'export'),
            ('humanresource', 'leave', 'view'),
            ('humanresource', 'leave', 'create'),
            ('humanresource', 'leave', 'approve'),
            
            # Housing
            ('housing', 'units', 'view'),
            ('housing', 'units', 'create'),
            ('housing', 'units', 'edit'),
            ('housing', 'units', 'delete'),
            ('housing', 'allocation', 'view'),
            ('housing', 'allocation', 'create'),
            ('housing', 'allocation', 'approve'),
            
            # Logistics
            ('logistics', 'inventory', 'view'),
            ('logistics', 'inventory', 'create'),
            ('logistics', 'inventory', 'edit'),
            ('logistics', 'inventory', 'export'),
            
            # Procurement
            ('procurement', 'requisition', 'view'),
            ('procurement', 'requisition', 'create'),
            ('procurement', 'requisition', 'approve'),
            
            # ICT
            ('ict', 'assets', 'view'),
            ('ict', 'assets', 'create'),
            ('ict', 'tickets', 'view'),
            ('ict', 'tickets', 'create'),
            
            # QHSE
            ('qhse', 'incidents', 'view'),
            ('qhse', 'incidents', 'report'),
            ('qhse', 'audit', 'view'),
            
            # General
            ('tickets', 'support', 'view'),
            ('tickets', 'support', 'create'),
        ]

        perms = {}
        for app, feature, action in permissions_data:
            obj, created = Permission.objects.get_or_create(
                app=app,
                feature=feature,
                action=action,
                defaults={'description': f'{action.capitalize()} {feature}'}
            )
            perms[(app, feature, action)] = obj
            if created:
                self.stdout.write(f'  ✓ Created permission: {app}.{feature}.{action}')

        # Assign permissions to levels
        role_permissions = [
            # CEO - all permissions
            ('Chief Executive Officer', [
                ('humanresource', 'staff', 'view'),
                ('humanresource', 'staff', 'create'),
                ('humanresource', 'staff', 'edit'),
                ('humanresource', 'staff', 'delete'),
                ('humanresource', 'staff', 'export'),
                ('humanresource', 'staff', 'import'),
                ('humanresource', 'petty_cash', 'view'),
                ('humanresource', 'petty_cash', 'approve'),
                ('housing', 'units', 'view'),
                ('housing', 'allocation', 'approve'),
                ('logistics', 'inventory', 'view'),
                ('procurement', 'requisition', 'approve'),
            ]),
            
            # CFO - financial focused
            ('Chief Financial Officer', [
                ('humanresource', 'staff', 'view'),
                ('humanresource', 'petty_cash', 'view'),
                ('humanresource', 'petty_cash', 'create'),
                ('humanresource', 'petty_cash', 'edit'),
                ('humanresource', 'petty_cash', 'approve'),
                ('humanresource', 'petty_cash', 'export'),
                ('procurement', 'requisition', 'view'),
                ('procurement', 'requisition', 'approve'),
            ]),
            
            # Director - manage department
            ('Director', [
                ('humanresource', 'staff', 'view'),
                ('humanresource', 'staff', 'create'),
                ('humanresource', 'staff', 'edit'),
                ('humanresource', 'staff', 'export'),
                ('humanresource', 'leave', 'view'),
                ('humanresource', 'leave', 'approve'),
                ('humanresource', 'petty_cash', 'view'),
                ('humanresource', 'petty_cash', 'create'),
                ('housing', 'units', 'view'),
                ('housing', 'allocation', 'view'),
            ]),
            
            # Manager - moderate permissions
            ('Manager', [
                ('humanresource', 'staff', 'view'),
                ('humanresource', 'petty_cash', 'view'),
                ('humanresource', 'petty_cash', 'create'),
                ('humanresource', 'leave', 'view'),
                ('housing', 'units', 'view'),
                ('logistics', 'inventory', 'view'),
            ]),
            
            # Supervisor - limited permissions
            ('Supervisor', [
                ('humanresource', 'staff', 'view'),
                ('humanresource', 'petty_cash', 'view'),
                ('humanresource', 'leave', 'view'),
                ('housing', 'units', 'view'),
                ('logistics', 'inventory', 'view'),
            ]),
            
            # Staff - basic view permissions
            ('Staff', [
                ('humanresource', 'leave', 'create'),
                ('humanresource', 'leave', 'view'),
                ('tickets', 'support', 'view'),
                ('tickets', 'support', 'create'),
            ]),
            
            # Intern - minimal access
            ('Intern', [
                ('tickets', 'support', 'view'),
            ]),
        ]

        for org_level_name, perms_list in role_permissions:
            org_level = org_levels.get(org_level_name)
            if not org_level:
                continue
            
            for app, feature, action in perms_list:
                perm = perms.get((app, feature, action))
                if not perm:
                    continue
                
                obj, created = RolePermission.objects.get_or_create(
                    organizational_level=org_level,
                    permission=perm
                )
                if created:
                    self.stdout.write(f'  ✓ Assigned: {org_level_name} → {app}.{feature}.{action}')

        self.stdout.write(self.style.SUCCESS('✓ Permission initialization complete!'))
        self.stdout.write(self.style.WARNING('\nNext steps:'))
        self.stdout.write('  1. Go to Django Admin: /admin/')
        self.stdout.write('  2. Assign organizational levels to user profiles')
        self.stdout.write('  3. Test access by logging in as different users')
