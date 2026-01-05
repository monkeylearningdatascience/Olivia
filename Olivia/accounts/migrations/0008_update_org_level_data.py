# Generated data migration to update organizational levels

from django.db import migrations


def update_organizational_levels(apps, schema_editor):
    """Update organizational level records to match new hierarchy"""
    OrganizationalLevel = apps.get_model('accounts', 'OrganizationalLevel')
    
    # Delete all existing organizational levels
    OrganizationalLevel.objects.all().delete()
    
    # Create new organizational levels
    new_levels = [
        {'name': 'Project Manager', 'level': 1, 'description': 'Highest authority - Project level management'},
        {'name': 'Operations Manager', 'level': 2, 'description': 'Operations level management'},
        {'name': 'Manager', 'level': 3, 'description': 'Department/Section management'},
        {'name': 'Officer / Engineer', 'level': 4, 'description': 'Professional/Technical staff'},
        {'name': 'Supervisor', 'level': 5, 'description': 'Team supervision and coordination'},
    ]
    
    for level_data in new_levels:
        OrganizationalLevel.objects.create(**level_data)


def reverse_migration(apps, schema_editor):
    """Reverse the changes - restore old levels"""
    OrganizationalLevel = apps.get_model('accounts', 'OrganizationalLevel')
    
    # Delete new levels
    OrganizationalLevel.objects.all().delete()
    
    # Restore old levels (optional - for rollback)
    old_levels = [
        {'name': 'Chief Executive Officer', 'level': 1, 'description': ''},
        {'name': 'Chief Financial Officer', 'level': 2, 'description': ''},
        {'name': 'Director', 'level': 2, 'description': ''},
        {'name': 'Manager', 'level': 3, 'description': ''},
        {'name': 'Supervisor', 'level': 4, 'description': ''},
        {'name': 'Team Lead', 'level': 5, 'description': ''},
        {'name': 'Staff', 'level': 6, 'description': ''},
        {'name': 'Intern', 'level': 7, 'description': ''},
    ]
    
    for level_data in old_levels:
        OrganizationalLevel.objects.create(**level_data)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_update_organizational_levels'),
    ]

    operations = [
        migrations.RunPython(update_organizational_levels, reverse_migration),
    ]
