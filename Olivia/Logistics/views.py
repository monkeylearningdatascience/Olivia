from django.shortcuts import render, redirect, get_object_or_404
from Olivia.constants import LOGISTICS_TABS

def logistics_home(request):
    return render(request, "logistics/home.html", {"tabs": LOGISTICS_TABS, "active_tab": "logistics_home"})


def logistics_tab_view(request, tab_name=None, **kwargs):
    # Allow tab_name to come from kwargs if not passed directly
    if not tab_name:
        tab_name = kwargs.get('tab_name')

    from django.http import Http404
    # Find the tab in LOGISTICS_TABS
    tab = next((t for t in LOGISTICS_TABS if t['url_name'] == tab_name), None)
    if not tab:
        raise Http404(f"Tab '{tab_name}' not found.")

    # Template path
    template_name = f"logistics/{tab_name.replace('logistics_', '')}.html"

    context = {
        "tabs": LOGISTICS_TABS,
        "active_tab": tab_name,
    }
    return render(request, template_name, context)