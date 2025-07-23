from django.urls import path
from .views import *

urlpatterns = [
    path('reports/monthly/<int:year>/<int:month>/', monthly_report_view, name='monthly-report'),
    path('reports/statistics/', monthly_statistics_view, name='monthly-statistics'),
    path('orders/recent/', recent_orders_view, name='recent-orders'),
    path('api/v1/user_order_list/', user_order_list),
    path('api/v1/employee_order_list/<int:employee_id>/',employee_order_list_by_id),
    path('api/v1/all_purchase_list/', user_order_product_list),
    path('api/v1/daily-category-spending/', daily_category_spending),
    path('api/v1/cost-summary/',category_cost_summary),
    path('admin-dashboard/',admin_dashboard, name='admin_dashboard'),
    path('employee-dashboard/', employee_dashboard, name='employee_dashboard'),
    path('api/v1/product-cost-summary/', product_cost_summary),
    path('api/v1/employee/daily-spending/<int:employee_id>', daily_employee_category_spending, name='daily_employee_spending'),
    path('employee/recent-orders/<int:employee_id>', recent_orders_by_employee_view, name='recent_orders_by_employee'),
    
    
]
