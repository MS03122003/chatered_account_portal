from django.shortcuts import render, redirect,get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth import logout as auth_logout
from .models import Employee  # Assuming you have an Employee model defined
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Service, Lead, LeadService
import json



def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if username == 'admin' and password == 'admin123':
            return render(request, 'dashboard.html')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    return render(request, 'login.html')


# Dashboard view

def dashboard(request):

    return render(request, 'dashboard.html')

def new_lead(request):
    services = Service.objects.all()
    
    if request.method == 'POST':
        try:
            # Create Lead
            lead = Lead.objects.create(
                customer_id=request.POST.get('customer_id'),
                customer_name=request.POST.get('customer_name'),
                mobile_no=request.POST.get('mobile_no'),
                father_name=request.POST.get('father_name'),
                spouse_name=request.POST.get('spouse_name'),
                mother_name=request.POST.get('mother_name'),
                aadhar_card_no=request.POST.get('aadhar_card_no'),
                pan_no=request.POST.get('pan_no'),
                company_name=request.POST.get('company_name'),
                email_id=request.POST.get('email_id'),
                gst_no=request.POST.get('gst_no'),
                cin_no=request.POST.get('cin_no'),
                assigned_to=request.POST.get('assigned_to'),
                delivery_date=request.POST.get('delivery_date') if request.POST.get('delivery_date') else None,
                upload_document=request.FILES.get('upload_document'),
                note=request.POST.get('note')
            )
            
            # Handle selected services (from session storage)
            selected_services = request.POST.get('selected_services')
            if selected_services:
                services_data = json.loads(selected_services)
                for service_data in services_data:
                    service = Service.objects.get(id=service_data['id'])
                    LeadService.objects.create(
                        lead=lead,
                        service=service,
                        service_price=service_data['price']
                    )
            
            messages.success(request, 'Lead created successfully!')
            return redirect('new_lead')
            
        except Exception as e:
            messages.error(request, f'Error creating lead: {str(e)}')
    
    return render(request, 'new_lead.html', {'services': services})

def customer(request):
    leads = Lead.objects.all()
    return render(request, 'customer.html', {'leads': leads})

def add_services(request):
    services = Service.objects.all()
    
    if request.method == 'POST':
        try:
            service = Service.objects.create(
                name=request.POST.get('service_name'),
                category=request.POST.get('category'),
                base_price=request.POST.get('base_price'),
                description=request.POST.get('description')
            )
            messages.success(request, 'Service added successfully!')
            return redirect('add_services')
        except Exception as e:
            messages.error(request, f'Error adding service: {str(e)}')
    
    return render(request, 'add_services.html', {'services': services})

def edit_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    
    if request.method == 'POST':
        try:
            service.name = request.POST.get('service_name')
            service.category = request.POST.get('category')
            service.base_price = request.POST.get('base_price')
            service.description = request.POST.get('description')
            service.save()
            messages.success(request, 'Service updated successfully!')
            return redirect('add_services')
        except Exception as e:
            messages.error(request, f'Error updating service: {str(e)}')
    
    return render(request, 'edit_service.html', {'service': service})

def delete_service(request, service_id):
    if request.method == 'POST':
        try:
            service = get_object_or_404(Service, id=service_id)
            service.delete()
            messages.success(request, 'Service deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting service: {str(e)}')
    
    return redirect('add_services')

def get_service_price(request, service_id):
    """API endpoint to get service price"""
    try:
        service = Service.objects.get(id=service_id)
        return JsonResponse({
            'success': True,
            'price': float(service.base_price),
            'name': service.name
        })
    except Service.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Service not found'
        })

# Add Employee view
def add_employee(request):
    error_message = ""
    if request.method == "POST":
        # Get user inputs (strip to avoid spaces)
        employee_id = request.POST.get('employee_id', '').strip()
        employee_name = request.POST.get('employee_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()

        # Manual validation
        if not all([employee_id, employee_name, phone_number, email, address]):
            error_message = "All fields are required!"
        elif Employee.objects.filter(employee_id=employee_id).exists():
            error_message = "Employee ID already exists!"
        elif not phone_number.isdigit() or len(phone_number) < 7:
            error_message = "Enter a valid phone number!"
        elif '@' not in email or '.' not in email:
            error_message = "Enter a valid email address!"
        else:
            Employee.objects.create(
                employee_id=employee_id,
                employee_name=employee_name,
                phone_number=phone_number,
                email=email,
                address=address
            )
            return redirect('employee_list')  # adjust to your employee list view name

    return render(request, "add_employee.html", {"error_message": error_message})
# Employee List view
def employee_list(request):
    employees = Employee.objects.all().order_by('employee_id')
    return render(request, "employee_list.html", {"employees": employees})

def edit_employee(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    if request.method == 'POST':
        # Handle form submission here, e.g.:
        # Update fields from request.POST
        # employee.employee_name = request.POST.get('employee_name')
        # employee.phone_number = request.POST.get('phone_number')
        # etc.
        # employee.save()
        return redirect('employee_list')
    else:
        context = {'employee': employee}
        return render(request, 'edit_employee.html', context)
    
@require_POST
def delete_employee(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    employee.delete()
    return redirect('employee_list')

# Logout view (POST method preferred for logout)
def logout_view(request):
    if request.method == 'POST':
        auth_logout(request)
        return redirect('login')  # change 'login' to your login page url name
    return redirect('dashboard')
