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

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import csv



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

# def new_lead(request):
#     if request.method == 'POST':
#         # Read form fields
#         customer_id = request.POST.get('customer_id')
#         customer_name = request.POST.get('customer_name')
#         mobile_no = request.POST.get('mobile_no')
#         father_name = request.POST.get('father_name')
#         spouse_name = request.POST.get('spouse_name')
#         mother_name = request.POST.get('mother_name')
#         aadhar_card_no = request.POST.get('aadhar_card_no')
#         pan_no = request.POST.get('pan_no')
#         company_name = request.POST.get('company_name')
#         email_id = request.POST.get('email_id')
#         gst_no = request.POST.get('gst_no')
#         cin_no = request.POST.get('cin_no')
#         assigned_to = request.POST.get('assigned_to')
#         delivery_date = request.POST.get('delivery_date') or None
#         note = request.POST.get('note')
#         upload_document = request.FILES.get('upload_document')

#         try:
#             lead = Lead.objects.create(
#                 customer_id=customer_id,
#                 customer_name=customer_name,
#                 mobile_no=mobile_no,
#                 father_name=father_name,
#                 spouse_name=spouse_name,
#                 mother_name=mother_name,
#                 aadhar_card_no=aadhar_card_no,
#                 pan_no=pan_no,
#                 company_name=company_name,
#                 email_id=email_id,
#                 gst_no=gst_no,
#                 cin_no=cin_no,
#                 assigned_to=assigned_to,
#                 delivery_date=delivery_date,
#                 note=note,
#                 upload_document=upload_document,
#             )
#             lead.save()

#             # Handle selected services JSON if sent
#             selected_services_json = request.POST.get('selected_services', '[]')
#             if selected_services_json and selected_services_json != '[]':
#                 import json
#                 from .models import LeadService, Service
#                 services_data = json.loads(selected_services_json)
#                 for sdata in services_data:
#                     service = Service.objects.get(id=sdata['id'])
#                     LeadService.objects.create(
#                         lead=lead,
#                         service=service,
#                         service_price=sdata['price']
#                     )

#             from django.contrib import messages
#             messages.success(request, 'Lead added successfully!')
#             return redirect('customer_list')  # Redirect to list

#         except Exception as e:
#             from django.contrib import messages
#             messages.error(request, f"Error saving lead: {e}")

#     # GET request
#     from .models import Service
#     services = Service.objects.all()
#     return render(request, 'new_lead.html', {'services': services})

# def customer(request):
#     leads = Lead.objects.all()
#     return render(request, 'customer.html', {'leads': leads})

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

# #customer
# def customer_detail(request, customer_id):
#     """Return lead (customer) details as JSON"""
#     customer = get_object_or_404(Lead, id=customer_id)

#     # Prepare list of related services
#     services = []
#     customer_services = LeadService.objects.filter(lead=customer).select_related('service')
#     for cs in customer_services:
#         services.append({
#             'name': cs.service.name,
#             'price': float(cs.service_price)
#         })

#     data = {
#         'customer_id': customer.customer_id,
#         'customer_name': customer.customer_name,
#         'mobile_no': customer.mobile_no,
#         'email_id': customer.email_id or '',
#         'father_name': customer.father_name or '',
#         'spouse_name': customer.spouse_name or '',
#         'mother_name': customer.mother_name or '',
#         'company_name': customer.company_name or '',
#         'pan_no': customer.pan_no or '',
#         'aadhar_card_no': customer.aadhar_card_no or '',
#         'gst_no': customer.gst_no or '',
#         'cin_no': customer.cin_no or '',
#         'note': customer.note or '',
#         'services': services,
#         'created_at': customer.created_at.strftime('%d %B, %Y'),
#     }

#     return JsonResponse(data)


# @login_required
# def edit_customer(request, customer_id):
#     """Edit Lead (Customer) and update their services"""
#     customer = get_object_or_404(Lead, id=customer_id)

#     if request.method == 'POST':
#         try:
#             customer.customer_id = request.POST.get('customer_id')
#             customer.customer_name = request.POST.get('customer_name')
#             customer.mobile_no = request.POST.get('mobile_no')
#             customer.father_name = request.POST.get('father_name', '')
#             customer.spouse_name = request.POST.get('spouse_name', '')
#             customer.mother_name = request.POST.get('mother_name', '')
#             customer.aadhar_card_no = request.POST.get('aadhar_card_no', '')
#             customer.pan_no = request.POST.get('pan_no', '')
#             customer.company_name = request.POST.get('company_name', '')
#             customer.email_id = request.POST.get('email_id', '')
#             customer.gst_no = request.POST.get('gst_no', '')
#             customer.cin_no = request.POST.get('cin_no', '')
#             customer.note = request.POST.get('note', '')

#             # Handle file upload
#             if 'upload_document' in request.FILES:
#                 customer.upload_document = request.FILES['upload_document']

#             customer.save()

#             # Update LeadService relations
#             selected_services_json = request.POST.get('selected_services', '[]')
#             if selected_services_json and selected_services_json != '[]':
#                 # Delete existing services
#                 LeadService.objects.filter(lead=customer).delete()

#                 services_data = json.loads(selected_services_json)
#                 for service_data in services_data:
#                     service_obj = Service.objects.get(id=service_data['id'])
#                     LeadService.objects.create(
#                         lead=customer,
#                         service=service_obj,
#                         service_price=float(service_data['price'])
#                     )

#             messages.success(request, f'Customer "{customer.customer_name}" has been updated successfully!')
#             return redirect('customer_list')

#         except Exception as e:
#             messages.error(request, f'Error updating customer: {str(e)}')

#     # For GET request, prepare current services & all services for form
#     current_services = []
#     customer_services = LeadService.objects.filter(lead=customer).select_related('service')
#     for cs in customer_services:
#         current_services.append({
#             'id': cs.service.id,
#             'name': cs.service.name,
#             'price': float(cs.service_price)
#         })

#     services = Service.objects.all()

#     context = {
#         'customer': customer,
#         'services': services,
#         'current_services': json.dumps(current_services),  # JSON string for JS use in template
#     }
#     return render(request, 'edit_customer.html', context)


# @require_POST
# @csrf_exempt  # Optional; remove if you want csrf protection on delete
# @login_required
# def delete_customer(request, customer_id):
#     """Delete lead (customer) and related lead services"""
#     try:
#         customer = get_object_or_404(Lead, id=customer_id)
#         customer_name = customer.customer_name

#         # Delete related LeadServices
#         LeadService.objects.filter(lead=customer).delete()

#         # Delete the customer itself
#         customer.delete()

#         messages.success(request, f'Customer "{customer_name}" has been deleted successfully!')
#         return JsonResponse({'success': True})

#     except Exception as e:
#         return JsonResponse({'success': False, 'error': str(e)}, status=400)

# Logout view (POST method preferred for logout)
def logout_view(request):
    if request.method == 'POST':
        auth_logout(request)
        return redirect('login')  # change 'login' to your login page url name
    return redirect('dashboard')

def new_lead(request):
    if request.method == 'POST':
        # Extract form data
        customer_id = request.POST.get('customer_id')
        customer_name = request.POST.get('customer_name')
        mobile_no = request.POST.get('mobile_no')
        father_name = request.POST.get('father_name')
        spouse_name = request.POST.get('spouse_name')
        mother_name = request.POST.get('mother_name')
        aadhar_card_no = request.POST.get('aadhar_card_no')
        pan_no = request.POST.get('pan_no')
        company_name = request.POST.get('company_name')
        email_id = request.POST.get('email_id')
        gst_no = request.POST.get('gst_no')
        cin_no = request.POST.get('cin_no')
        assigned_to = request.POST.get('assigned_to')
        delivery_date = request.POST.get('delivery_date') or None
        note = request.POST.get('note')
        upload_document = request.FILES.get('upload_document')

        try:
            # Create Lead object
            lead = Lead.objects.create(
                customer_id=customer_id,
                customer_name=customer_name,
                mobile_no=mobile_no,
                father_name=father_name,
                spouse_name=spouse_name,
                mother_name=mother_name,
                aadhar_card_no=aadhar_card_no,
                pan_no=pan_no,
                company_name=company_name,
                email_id=email_id,
                gst_no=gst_no,
                cin_no=cin_no,
                assigned_to=assigned_to,
                delivery_date=delivery_date,
                note=note,
                upload_document=upload_document,
            )
            

            # Process selected services JSON (from hidden input)
            selected_services_json = request.POST.get('selected_services', '[]')
            if selected_services_json and selected_services_json != '[]':
                services_data = json.loads(selected_services_json)
                for service_data in services_data:
                    service = Service.objects.get(id=service_data['id'])
                    LeadService.objects.create(
                        lead=lead,
                        service=service,
                        service_price=service_data['price']
                    )

            messages.success(request, 'Lead added successfully!')
            return redirect('customer')  # Redirect to customer list page

        except Exception as e:
            messages.error(request, f"Error saving lead: {e}")

    # GET: Render form with existing services for dropdown
    services = Service.objects.all()
    return render(request, 'new_lead.html', {'services': services})





def customer(request):
    # Fetch all leads ordered by newest first
    leads = Lead.objects.all().order_by('-created_at')
    return render(request, 'customer.html', {'leads': leads})




def edit_customer(request, customer_id):
    customer = get_object_or_404(Lead, id=customer_id)

    if request.method == 'POST':
        try:
            customer.customer_id = request.POST.get('customer_id')
            customer.customer_name = request.POST.get('customer_name')
            customer.mobile_no = request.POST.get('mobile_no')
            customer.father_name = request.POST.get('father_name', '')
            customer.spouse_name = request.POST.get('spouse_name', '')
            customer.mother_name = request.POST.get('mother_name', '')
            customer.aadhar_card_no = request.POST.get('aadhar_card_no', '')
            customer.pan_no = request.POST.get('pan_no', '')
            customer.company_name = request.POST.get('company_name', '')
            customer.email_id = request.POST.get('email_id', '')
            customer.gst_no = request.POST.get('gst_no', '')
            customer.cin_no = request.POST.get('cin_no', '')
            customer.note = request.POST.get('note', '')

            if 'upload_document' in request.FILES:
                customer.upload_document = request.FILES['upload_document']

            customer.save()

            selected_services_json = request.POST.get('selected_services', '[]')
            if selected_services_json and selected_services_json != '[]':
                LeadService.objects.filter(lead=customer).delete()
                services_data = json.loads(selected_services_json)
                for service_data in services_data:
                    service_obj = Service.objects.get(id=service_data['id'])
                    LeadService.objects.create(
                        lead=customer,
                        service=service_obj,
                        service_price=service_data['price']
                    )

            messages.success(request, f'Customer "{customer.customer_name}" updated successfully!')
            return redirect('customer_list')

        except Exception as e:
            messages.error(request, f'Error updating customer: {str(e)}')

    # For GET request - load current services & all services for selection
    current_services = []
    customer_services = LeadService.objects.filter(lead=customer).select_related('service')
    for cs in customer_services:
        current_services.append({
            'id': cs.service.id,
            'name': cs.service.name,
            'price': float(cs.service_price)
        })

    services = Service.objects.all()
    context = {
        'customer': customer,
        'services': services,
        'current_services': json.dumps(current_services),
    }
    return render(request, 'edit_customer.html', context)


@require_POST
@csrf_exempt  # Optionally remove @csrf_exempt for better security

def delete_customer(request, customer_id):
    try:
        customer = get_object_or_404(Lead, id=customer_id)
        customer_name = customer.customer_name

        LeadService.objects.filter(lead=customer).delete()
        customer.delete()

        messages.success(request, f'Customer "{customer_name}" deleted successfully!')
        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)