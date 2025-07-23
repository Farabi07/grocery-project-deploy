from django.urls import path
from .views import employee_receipt_scan_view,receipt_scan_view

urlpatterns = [
    path('scan-receipt/', receipt_scan_view),
    path('employee/scan-receipt/<int:employee_id>/', employee_receipt_scan_view, name='scan_receipt'),
]