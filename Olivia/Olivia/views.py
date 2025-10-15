from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .constants import DEPARTMENTS
from .constants import HR_TABS

def departments_context(request):
    return {"departments": DEPARTMENTS}

@login_required
def dashboard(request):
    return render(request, 'dashboard.html', {'departments': DEPARTMENTS})

def logout(request):
    return render(request, 'logout.html')

