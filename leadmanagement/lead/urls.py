from django.urls import path
from .views import login_view
from . import views

urlpatterns = [
    path('', login_view, name='root_login'),
    path('login/', login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('new-lead/', views.new_lead, name='new_lead'),
    path('customer/', views.customer, name='customer'),
    path('add-services/', views.add_services, name='add_services'),
    path('add-employee/', views.add_employee, name='add_employee'),
    path('logout/', views.logout_view, name='logout'),
] 