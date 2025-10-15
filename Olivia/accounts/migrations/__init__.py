from django.db import migrations

def create_initial_apps(apps, schema_editor):
    AppAccess = apps.get_model("accounts", "AppAccess")
    apps_to_create = [
        ("humanresource", "Human Resource"),
        ("housing", "Housing & Tenants"),
        ("hardservice", "Hard Services"),
        ("softservice", "Soft Services"),
        ("utility", "Utility"),
        ("fls", "Fire Light & Safety"),
        ("logistics", "Logistics"),
        ("procurement", "Procurement"),
        ("warehouse", "Warehouse"),
        ("qhse", "QHSE"),
        ("ict", "Information Technology"),
        ("ticket", "Ticketing"),
        ("training", "Training"),
    ]
    for code, name in apps_to_create:
        AppAccess.objects.get_or_create(code=code, defaults={"name": name})

def remove_initial_apps(apps, schema_editor):
    AppAccess = apps.get_model("accounts", "AppAccess")
    AppAccess.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_initial_apps, remove_initial_apps),
    ]
