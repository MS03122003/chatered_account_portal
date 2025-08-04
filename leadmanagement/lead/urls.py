from django.urls import path
from .views import login_view
from . import views

urlpatterns = [
    path('', login_view, name='root_login'),
    path('login/', login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('new-lead/', views.new_lead, name='new_lead'),
    path('customer/', views.customer,name='customer'),
    path('customer/edit/<int:customer_id>/', views.edit_customer, name='edit_customer'),
    path('customer/delete/<int:customer_id>/', views.delete_customer, name='delete_customer'),
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

    path('add-task/', views.add_task, name='add_task'),
    path('task-list/', views.task_list, name='task_list'),
    path('task/edit/<int:task_id>/', views.edit_task, name='edit_task'),
    path('task/delete/<int:task_id>/', views.delete_task, name='delete_task'),
    path('task/detail/<int:task_id>/', views.task_detail, name='task_detail'),
    path('task/update-status/<int:task_id>/', views.update_task_status, name='update_task_status'),
] 