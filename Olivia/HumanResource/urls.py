from django.urls import path
from . import views

urlpatterns = [
    path('', views.humanresource_home, name="humanresource_home"),
    path('leave/', views.hr_leave, name='hr_leave'),
    path('work-notice/', views.hr_work_notice, name='hr_work_notice'),
    path('clearance/', views.hr_clearance, name='hr_clearance'),
    path('work-letters/', views.hr_work_letters, name='hr_work_letters'),
    path('medical-declarations/', views.hr_medical_declarations, name='hr_medical_declarations'),
    path('staff-hiring-evaluation/', views.hr_staff_hiring_eval, name='hr_staff_hiring_evaluation'),
    path('transfer-request/', views.hr_transfer_request, name='hr_transfer_request'),
    path('contract-amendments/', views.hr_contract_amendments, name='hr_contract_amendments'),
    path('contract-termination/', views.hr_contract_termination, name='hr_contract_termination'),
    path('monthly-attendance/', views.hr_monthly_attendance, name='hr_monthly_attendance'),
    path('overtime/', views.hr_overtime, name='hr_overtime'),
    path('petty-cash/', views.hr_petty_cash, name='hr_petty_cash'),
    path('update_balance_entry/', views.update_balance_entry, name='update_balance_entry'),
    path('export/petty-cash/', views.export_petty_cash, name='export_petty_cash'),
    path('create_balance_entry/', views.create_balance_entry, name='create_balance_entry'),
    path('get_submitted_total/', views.get_submitted_total, name='get_submitted_total'),  
]