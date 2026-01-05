# constants.py
from django.shortcuts import render

# HR Tabs
HR_TABS = [
    {"name": "Petty Cash", "url_name": "hr_petty_cash"},
    {"name": "Staff", "url_name": "hr_staff"},
    {"name": "Leave", "url_name": "hr_leave"},
    {"name": "Notice", "url_name": "hr_work_notice"},
    {"name": "Clearance", "url_name": "hr_clearance"},
    {"name": "Letters", "url_name": "hr_work_letters"},
    {"name": "Declarations", "url_name": "hr_medical_declarations"},
    {"name": "Hiring", "url_name": "hr_hiring"},
    {"name": "Transfer", "url_name": "hr_transfer_request"},
    {"name": "Amendments", "url_name": "hr_contract_amendments"},
    {"name": "Termination", "url_name": "hr_contract_termination"},
    {"name": "Attendance", "url_name": "hr_monthly_attendance"},
    {"name": "Overtime", "url_name": "hr_overtime"},
]

# Example: Departments (you already had this in views.py earlier)
DEPARTMENTS = [
    {'name': 'HumanResource', 'url': '/humanresource/', 'icon': 'fa-solid fa-user'},
    # {'name': 'Housing', 'url': '/housing/', 'icon': 'fa-solid fa-home'},  # Hidden - can be enabled in future
    {'name': 'Hard Service', 'url': '/hardservice/', 'icon': 'fa-solid fa-screwdriver-wrench'},
    {'name': 'Soft Service', 'url': '/softservice/', 'icon': 'fa-solid fa-broom'},
    {'name': 'Utility', 'url': '/utility/', 'icon': 'fa-solid fa-bolt'},
    {'name': 'FLS', 'url': '/fls/', 'icon': 'fa-solid fa-fire-extinguisher'},
    {'name': 'Logistics', 'url': '/logistics/', 'icon': 'fa-solid fa-truck'},
    {'name': 'Procurement', 'url': '/procurement/', 'icon': 'fa-solid fa-cart-shopping'},
    {'name': 'Warehouse', 'url': '/warehouse/', 'icon': 'fa-solid fa-box'},
    {'name': 'QHSE', 'url': '/qhse/', 'icon': 'fa-solid fa-shield-halved'},
    {'name': 'ICT', 'url': '/ict/', 'icon': 'fa-solid fa-computer'},
    # {'name': 'Tickets', 'url': '/tickets/', 'icon': 'fa-solid fa-ticket'},  # Hidden - can be enabled in future
    {'name': 'Training', 'url': '/training/', 'icon': 'fa-solid fa-chalkboard-teacher'},
]

HOUSING_TABS = [
    {"name": "Units", "url_name": "units"},
    # {"name": "Company Group", "url_name": "group"},
    {"name": "Company", "url_name": "company"},
    {"name": "User", "url_name": "user"},
    {"name": "Allocation", "url_name": "allocation"},
    {"name": "Assigning", "url_name": "assigning"},
    {"name": "Reservation", "url_name": "reservation"},
    {"name": "Check In/Out", "url_name": "checkin_checkout"},
    {"name": "Keylog", "url_name": "tarka"},
    {"name": "Parcel", "url_name": "parcel"},
    {"name": "Visitor", "url_name": "visitor"},
    ]

LOGISTICS_TABS = [
    # {"name": "Home", "url_name": "logistics_home"},
    {"name": "Vehicle Request", "url_name": "logistics_vehicle_request"},
    {"name": "Vehicle Log", "url_name": "logistics_vehicle_log"},
    {"name": "Driver Log", "url_name": "logistics_driver_log"},
    {"name": "Service Details", "url_name": "logistics_service_details"},
    {"name": "Vehicle Transfer", "url_name": "logistics_vehicle_transfer"},
    ]

WAREHOUSE_TABS = [
    {"name": "Receiving", "url_name": "receiving"},
    {"name": "Dispatch", "url_name": "dispatch"},
    {"name": "Closing Stock", "url_name": "closing_stock"},
    {"name": "Inventory", "url_name": "inventory"},
    {"name": "Stock Movement", "url_name": "stock_movement"},
    {"name": "Stock Adjustment", "url_name": "stock_adjustment"},
    {"name": "Stock Alert", "url_name": "stock_alert"},
    {"name": "Material Requisition", "url_name": "material_requisition"},
    {"name": "Label Generator", "url_name": "label_generator"},
]

QHSE_TABS = [
    {"name": "Policies", "url_name": "policies"},
    {"name": "Rules", "url_name": "rules"},
    {"name": "ERP", "url_name": "erp"},
    {"name": "RAMS", "url_name": "rams"},
    {"name": "Induction", "url_name": "induction"},
    {"name": "Trainings", "url_name": "trainings"},
    {"name": "TBT's", "url_name": "tbts"},
    {"name": "Observations", "url_name": "observations"},
    {"name": "Permit Issuance", "url_name": "permit"},
    {"name": "Incidents", "url_name": "incidents"},
    {"name": "Inspection", "url_name": "inspection"},
]

# Context processor for departments
def departments_context(request):
    return {"departments": DEPARTMENTS}

# Context processor for HR tabs
def hr_tabs_context(request):
    return {"HR_TABS": HR_TABS}