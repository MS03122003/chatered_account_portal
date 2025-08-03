from django.urls import path
from .views import login_view
from . import views

urlpatterns = [
    path('', login_view, name='root_login'),
    path('login/', login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('new-lead/', views.new_lead, name='new_lead'),
    path('customer/', views.customer, name='customer'),
    # service
    path('add-services/', views.add_services, name='add_services'),
    path('edit-service/<int:service_id>/', views.edit_service, name='edit_service'),
    path('delete-service/<int:service_id>/', views.delete_service, name='delete_service'),
    
    path('logout/', views.logout_view, name='logout'),

    # Employee management
    path('add-employee/', views.add_employee, name='add_employee'),
    path('employee_list/',views.employee_list, name='employee_list'),
    path('employee/edit/<int:employee_id>/', views.edit_employee, name='edit_employee'),
    path('employee/delete/<int:employee_id>/', views.delete_employee, name='delete_employee'),
] 