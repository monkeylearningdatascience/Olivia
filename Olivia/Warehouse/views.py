from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from Olivia.constants import WAREHOUSE_TABS
from .models import Receiving, ReceivingItem, Supplier
from django_countries import countries
import json
from datetime import datetime

# Create your views here.
def home(request):
    context = {
        'tabs': WAREHOUSE_TABS,
        'active_tab': None
    }
    return render(request, "warehouse/home.html", context)

# Tab Views
def receiving_list(request):
    # Prepare countries list
    countries_list = []
    try:
        countries_list = [{'code': c.code, 'name': c.name} for c in countries]
    except Exception as e:
        print(f"WARNING: Error processing countries: {e}")
        countries_list = []
    
    import time
    context = {
        'tabs': WAREHOUSE_TABS,
        'active_tab': 'receiving',
        'countries': countries_list,
        'timestamp': int(time.time())
    }
    return render(request, "warehouse/receiving.html", context)

def dispatch_list(request):
    context = {
        'tabs': WAREHOUSE_TABS,
        'active_tab': 'dispatch'
    }
    return render(request, "warehouse/dispatch.html", context)

def closing_stock_list(request):
    context = {
        'tabs': WAREHOUSE_TABS,
        'active_tab': 'closing_stock'
    }
    return render(request, "warehouse/closing_stock.html", context)

def inventory_list(request):
    context = {
        'tabs': WAREHOUSE_TABS,
        'active_tab': 'inventory'
    }
    return render(request, "warehouse/inventory.html", context)

def stock_movement_list(request):
    context = {
        'tabs': WAREHOUSE_TABS,
        'active_tab': 'stock_movement'
    }
    return render(request, "warehouse/stock_movement.html", context)

def stock_adjustment_list(request):
    context = {
        'tabs': WAREHOUSE_TABS,
        'active_tab': 'stock_adjustment'
    }
    return render(request, "warehouse/stock_adjustment.html", context)

def stock_alert_list(request):
    context = {
        'tabs': WAREHOUSE_TABS,
        'active_tab': 'stock_alert'
    }
    return render(request, "warehouse/stock_alert.html", context)

def material_requisition_list(request):
    context = {
        'tabs': WAREHOUSE_TABS,
        'active_tab': 'material_requisition'
    }
    return render(request, "warehouse/material_requisition.html", context)

def label_generator(request):
    context = {
        'tabs': WAREHOUSE_TABS,
        'active_tab': 'label_generator'
    }
    return render(request, "warehouse/label_generator.html", context)