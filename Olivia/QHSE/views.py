# qhse/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from Olivia.constants import QHSE_TABS # CRITICAL: Import the correct constants list


# --- 1. Home View ---
def qhse_home(request):
    """
    Renders the QHSE module home page.
    """
    # NOTE: Set active_tab to the first tab's url_name if you want to default to it, 
    # or keep 'qhse_home' if you have a distinct home template.
    return render(request, "qhse/home.html", {"tabs": QHSE_TABS, "active_tab": "qhse_home"})


# --- 2. Tab View (Handles all dynamic tabs) ---
def qhse_tab_view(request, tab_name=None, **kwargs):
    """
    Renders the specific template for a given QHSE tab.
    """
    if not tab_name:
        tab_name = kwargs.get('tab_name')

    # Find the tab in QHSE_TABS by matching the URL name
    tab = next((t for t in QHSE_TABS if t['url_name'] == tab_name), None)
    
    if not tab:
        # This is where your previous error was raised, and it's correct for the QHSE app.
        raise Http404(f"QHSE Tab '{tab_name}' not found.")

    # ✅ SIMPLIFIED: The template name is simply 'qhse/<url_name>.html'
    template_name = f"qhse/{tab['url_name']}.html"
    
    context = {
        "tabs": QHSE_TABS,
        "active_tab": tab_name, # The active tab is the simple url_name (e.g., 'inspection')
    }
    return render(request, template_name, context)