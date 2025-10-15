from django.db import migrations

def seed_app_access(apps, schema_editor):
    AppAccess = apps.get_model("accounts", "AppAccess")

    apps_to_add = [
        ("humanresource", "Human Resource"),
        ("housing", "Housing & Tenant"),
        ("hardservice", "Hard Service"),
        ("softservice", "Soft Service"),
        ("utility", "Utility"),
        ("fls", "Fire Light & Safety"),
        ("logistics", "Logistics"),
        ("procurement", "Procurement"),
        ("warehouse", "Warehouse"),
        ("qhse", "QHSE"),
        ("ict", "ICT"),
        ("ticket", "Ticketing"),
        ("training", "Training"),
    ]

    for code, name in apps_to_add:
        AppAccess.objects.get_or_create(code=code, defaults={"name": name})

def unseed_app_access(apps, schema_editor):
    AppAccess = apps.get_model("accounts", "AppAccess")
    AppAccess.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),  # replace with your real initial migration name
    ]

    operations = [
        migrations.RunPython(seed_app_access, unseed_app_access),
    ]
