from django.shortcuts import render, redirect,get_object_or_404
from django.http import HttpResponse, JsonResponse
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
from .models import Service, Lead, LeadService,Task
import json

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST,require_http_methods
import json
import csv
from decimal import Decimal
from django.db import transaction





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
    # Get search parameter
    search_query = request.GET.get('search', '').strip()
    
    # Base queryset with all necessary joins
    tasks = Task.objects.select_related(
        'customer_name', 
        'assigned_to', 
        'service_name'
    ).all()
    
    # Apply search filter if provided
    if search_query:
        tasks = tasks.filter(
            Q(customer_name__customer_name__icontains=search_query) |
            Q(customer_name__mobile_no__icontains=search_query) |
            Q(assigned_to__employee_name__icontains=search_query) |
            Q(assigned_to__phone_number__icontains=search_query) |
            Q(service_name__name__icontains=search_query) |
            Q(task_id__icontains=search_query) |
            Q(task_status__icontains=search_query) |
            Q(payment_status__icontains=search_query)
        )
    
    # Order by creation date (newest first)
    tasks = tasks.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(tasks, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    tasks_page = paginator.get_page(page_number)
    
    # Calculate dashboard statistics
    total_customers = Lead.objects.count()
    total_leads=Lead.objects.filter(lead_type='lead').count()
    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(task_status='completed').count()
    pending_tasks = Task.objects.filter(task_status__in=['assigned', 'in_progress']).count()
    
    # Today's statistics
    today = timezone.now().date()
    today_tasks = Task.objects.filter(created_at__date=today).count()
    
    # Overdue tasks
    overdue_tasks = Task.objects.filter(
        delivery_date__lt=today,
        task_status__in=['assigned', 'in_progress', 'on_hold']
    ).count()
    
    # Payment statistics
    total_revenue = Task.objects.aggregate(Sum('payment_amount'))['payment_amount__sum'] or 0
    paid_amount = Task.objects.filter(payment_status='paid').aggregate(Sum('payment_amount'))['payment_amount__sum'] or 0
    pending_amount = Task.objects.filter(payment_status='pending').aggregate(Sum('payment_amount'))['payment_amount__sum'] or 0
    
    context = {
        'tasks': tasks_page,
        'search_query': search_query,
        'total_customers': total_customers,
        'total_leads':total_leads,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'today_tasks': today_tasks,
        'overdue_tasks': overdue_tasks,
        'total_revenue': total_revenue,
        'paid_amount': paid_amount,
        'pending_amount': pending_amount,
    }
    
    return render(request, 'dashboard.html', context)

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
        designation=request.POST.get('designation','').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()

        # Manual validation
        if not all([employee_id, employee_name, phone_number, email]):
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
                designation=designation,
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

def new_lead(request):
    if request.method == 'POST':
        # Get submission type to determine where to save
        submission_type = request.POST.get('submission_type', 'lead')  # default to customer for backward compatibility
        
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
        document_name = request.POST.get('document_name', '').strip()
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
                document_name=document_name,
                upload_document=upload_document,
                lead_type='lead' if submission_type == 'lead' else 'customer'
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

            

            # # Later when creating Lead object:
            # lead = Lead.objects.create(
            #     # all the other fields...
                
            # )

            # Redirect based on submission type
            if submission_type == 'lead':
                messages.success(request, f'Lead "{customer_name}" has been saved successfully and added to All Leads!')
                return redirect('all_leads')  # Redirect to all leads page
            else:  # submission_type == 'customer'
                messages.success(request, f'Customer "{customer_name}" has been added successfully!')
                return redirect('customer')  # Redirect to customer list page

        except Exception as e:
            messages.error(request, f"Error saving lead: {e}")

    # GET: Render form with existing services for dropdown
    services = Service.objects.all()
    return render(request, 'new_lead.html', {'services': services})


def customer(request):
    # Fetch all leads ordered by newest first with their related services
    leads = Lead.objects.filter(lead_type='customer').order_by('-created_at')
    
    # Prepare customer data with services and total amounts
    customers = []
    for lead in leads:
        # Get services for this lead
        lead_services = LeadService.objects.filter(lead=lead).select_related('service')
        services = [{'name': ls.service.name, 'price': ls.service_price} for ls in lead_services]
        
        # Calculate total amount
        total_amount = sum(service['price'] for service in services)
        
        # Create a customer dictionary with lead data and additional fields
        customer = {
            'id': lead.id,
            'customer_id': lead.customer_id,
            'customer_name': lead.customer_name,
            'mobile_no': lead.mobile_no,
            'email_id': lead.email_id,
            'father_name': lead.father_name,
            'spouse_name': lead.spouse_name,
            'mother_name': lead.mother_name,
            'aadhar_card_no': lead.aadhar_card_no,
            'pan_no': lead.pan_no,
            'company_name': lead.company_name,
            'gst_no': lead.gst_no,
            'cin_no': lead.cin_no,
            'assigned_to': lead.assigned_to,
            'delivery_date': lead.delivery_date,
            'note': lead.note,
            'upload_document': lead.upload_document,
            'created_at': lead.created_at,
            'services': services,
            'total_amount': total_amount
        }
        customers.append(customer)
    
    # Calculate statistics
    total_customers = len(customers)
    today = timezone.now().date()
    active_today = len([c for c in customers if c['created_at'].date() == today])
    
    # This month
    start_of_month = today.replace(day=1)
    this_month = len([c for c in customers if c['created_at'].date() >= start_of_month])
    
    # Total revenue
    total_revenue = sum(c['total_amount'] for c in customers)

    paginator = Paginator(customers, 10)  # Show 10 customers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'customers': page_obj,  # This now contains paginated customers
        'page_obj': page_obj,   # For pagination controls in template
        'total_customers': total_customers,
        'active_today': active_today,
        'this_month': this_month,
        'total_revenue': total_revenue
    }
    
    
    return render(request, 'customer.html', context)


def customer_detail(request, customer_id):
    """Return lead (customer) details as JSON"""
    customer = get_object_or_404(Lead, id=customer_id)

    # Prepare list of related services
    services = []
    customer_services = LeadService.objects.filter(lead=customer).select_related('service')
    for cs in customer_services:
        services.append({
            'name': cs.service.name,
            'price': float(cs.service_price)
        })

    data = {
        'customer_id': customer.customer_id,
        'customer_name': customer.customer_name,
        'mobile_no': customer.mobile_no,
        'email_id': customer.email_id or '',
        'father_name': customer.father_name or '',
        'spouse_name': customer.spouse_name or '',
        'mother_name': customer.mother_name or '',
        'company_name': customer.company_name or '',
        'pan_no': customer.pan_no or '',
        'aadhar_card_no': customer.aadhar_card_no or '',
        'gst_no': customer.gst_no or '',
        'cin_no': customer.cin_no or '',
        'note': customer.note or '',
        'services': services,
        'created_at': customer.created_at.strftime('%d %B, %Y'),
    }

    paginator = Paginator(customers, 10)  # Show 10 customers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    

    return JsonResponse(data)


def edit_customer(request, customer_id):
    customer = get_object_or_404(Lead, id=customer_id)

    if request.method == 'POST':
        
        # 🔹 If Remove button clicked
        if 'delete_document' in request.POST:
            if customer.upload_document:
                customer.upload_document.delete(save=False)  # delete file from storage
                customer.upload_document = None
                customer.document_name = None
                customer.save()
                messages.success(request, "Document removed successfully.")
            return redirect('edit_customer', customer_id=customer.id)

        # 🔹 Normal update
        try:
            customer.customer_id = request.POST.get('customer_id', '').strip()
            customer.customer_name = request.POST.get('customer_name', '').strip()
            customer.mobile_no = request.POST.get('mobile_no', '').strip()
            customer.father_name = request.POST.get('father_name', '').strip()
            customer.spouse_name = request.POST.get('spouse_name', '').strip()
            customer.mother_name = request.POST.get('mother_name', '').strip()
            customer.aadhar_card_no = request.POST.get('aadhar_card_no', '').strip()
            customer.pan_no = request.POST.get('pan_no', '').strip()
            customer.company_name = request.POST.get('company_name', '').strip()
            customer.email_id = request.POST.get('email_id', '').strip()
            customer.gst_no = request.POST.get('gst_no', '').strip()
            customer.cin_no = request.POST.get('cin_no', '').strip()
            customer.note = request.POST.get('note', '').strip()

            # 🔹 Save document name from form
            customer.document_name = request.POST.get('document_name', '').strip()

            # 🔹 If a new file is uploaded, replace the old one
            if 'upload_document' in request.FILES:
                customer.upload_document = request.FILES['upload_document']

            customer.save()

            # 🔹 Update services
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
            return redirect('customer')

        except Exception as e:
            messages.error(request, f'Error updating customer: {str(e)}')

    # 🔹 For GET request - load current services & all services for selection
    current_services = []
    customer_services = LeadService.objects.filter(lead=customer).select_related('service')
    for cs in customer_services:
        current_services.append({
            'id': cs.service.id,
            'name': cs.service.name,
            'price': float(cs.service_price)
        })

    services = Service.objects.all()
    return render(request, 'edit_customer.html', {
        'customer': customer,
        'services': services,
        'current_services': json.dumps(current_services),
    })


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

def view_customer(request, customer_id):
    """Display detailed view of a specific customer"""
    customer = get_object_or_404(Lead, id=customer_id, lead_type='customer')
    customer_services = LeadService.objects.filter(lead=customer).select_related('service')
    total_amount = sum(cs.service_price for cs in customer_services)
    
    customer.total_amount = total_amount
    
    def get_document_filename():
        if customer.upload_document:
            return customer.upload_document.name.split('/')[-1]
        return None
    
    customer.get_document_filename = get_document_filename
    
    context = {
        'customer': customer,
        'services': customer_services,
        'total_amount': total_amount,
    }
    
    return render(request, 'view_customer.html', context)  

# Task management views (NEW)
def add_task(request):
    if request.method == 'POST':
        try:
            # Fetch form data
            assigned_to_id = request.POST.get('assigned_to')
            customer_name_id = request.POST.get('customer_name')
            service_name_id = request.POST.get('service_name')
            delivery_date = request.POST.get('delivery_date')
            payment_amount = Decimal(request.POST.get('payment_amount') or 0)
            amount_paid = Decimal(request.POST.get('amount_paid') or 0)
            payment_status = request.POST.get('payment_status')
            task_notes = request.POST.get('task_notes', '')

            assigned_to = Employee.objects.get(id=assigned_to_id)
            customer = Lead.objects.get(id=customer_name_id)
            service = Service.objects.get(id=service_name_id)

            # Calculate balance
            if payment_status == 'paid':
                amount_paid = payment_amount
                balance_amount = Decimal('0.00')
            elif payment_status == 'pending':
                amount_paid = Decimal('0.00')
                balance_amount = payment_amount
            else:  # partial
                balance_amount = max(payment_amount - amount_paid, Decimal('0.00'))

            # Save to DB
            task = Task.objects.create(
                assigned_to=assigned_to,
                customer_name=customer,
                service_name=service,
                delivery_date=delivery_date,
                payment_amount=payment_amount,
                amount_paid=amount_paid,
                balance_amount=balance_amount,
                payment_status=payment_status,
                task_notes=task_notes
            )

            messages.success(request, f"Task {task.task_id} created successfully!")
            return redirect('payment_list')

        except Exception as e:
            messages.error(request, f"Error creating task: {e}")

    employees = Employee.objects.all().order_by('employee_name')
    customers = Lead.objects.all().order_by('customer_name')
    services = Service.objects.all().order_by('name')

    return render(request, 'add_task.html', {
        'employees': employees,
        'customers': customers,
        'services': services
    })

def task_list(request):
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    employee_filter = request.GET.get('employee', '')
    search_query = request.GET.get('search', '')

    # Base queryset
    tasks = Task.objects.select_related('assigned_to', 'customer_name', 'service_name').all()

    # Apply filters
    if status_filter:
        tasks = tasks.filter(task_status=status_filter)
    
    if employee_filter:
        tasks = tasks.filter(assigned_to_id=employee_filter)
    
    if search_query:
        tasks = tasks.filter(
            Q(task_id__icontains=search_query) |
            Q(customer_name__customer_name__icontains=search_query) |
            Q(service_name__name__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page')
    tasks = paginator.get_page(page_number)

    # Statistics
    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(task_status='completed').count()
    pending_tasks = Task.objects.filter(task_status__in=['assigned', 'in_progress']).count()
    overdue_tasks = Task.objects.filter(
        delivery_date__lt=timezone.now().date(),
        task_status__in=['assigned', 'in_progress', 'on_hold']
    ).count()

    # Get employees for filter dropdown
    employees = Employee.objects.all().order_by('employee_name')

    context = {
        'tasks': tasks,
        'employees': employees,
        'status_filter': status_filter,
        'employee_filter': employee_filter,
        'search_query': search_query,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
    }
    return render(request, 'task_list.html', context)

def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == 'POST':
        try:
            assigned_id = request.POST.get('assigned_to')
            customer_id = request.POST.get('customer_name')
            service_id = request.POST.get('service_name')
            delivery_date = request.POST.get('delivery_date')
            payment_amount_raw = request.POST.get('payment_amount')
            payment_status = request.POST.get('payment_status')
            amount_paid_raw = request.POST.get('amount_paid', '0')
            balance_amount_raw = request.POST.get('balance_amount', '0')
            task_notes = request.POST.get('task_notes', '')

            # Convert decimals safely
            payment_amount = Decimal(payment_amount_raw) if payment_amount_raw else Decimal('0.00')
            amount_paid = Decimal(amount_paid_raw) if amount_paid_raw else Decimal('0.00')

            # Validate amount_paid and payment_amount
            if amount_paid < 0 or amount_paid > payment_amount:
                messages.error(request, "Amount paid must be between 0 and Total Amount.")
                raise ValueError("Invalid amount paid value.")

            # Calculate balance automatically unless you want manual override when 'balance' status
            if payment_status == 'paid':
                amount_paid = payment_amount
                balance_amount = Decimal('0.00')
            elif payment_status == 'pending':
                amount_paid = Decimal('0.00')
                balance_amount = payment_amount
            elif payment_status == 'partial':
                balance_amount = payment_amount - amount_paid
                if balance_amount < 0:
                    balance_amount = Decimal('0.00')
            else:
                # If you keep 'balance' as status, handle accordingly
                balance_amount = Decimal(balance_amount_raw) if balance_amount_raw else Decimal('0.00')

            # Update task fields
            task.assigned_to = Employee.objects.get(id=assigned_id)
            task.customer_name = Lead.objects.get(id=customer_id)
            task.service_name = Service.objects.get(id=service_id)
            task.delivery_date = delivery_date
            task.payment_amount = payment_amount
            task.payment_status = payment_status
            task.amount_paid = amount_paid
            task.balance_amount = balance_amount
            task.task_notes = task_notes

            task.save()

            messages.success(request, f"Task {task.task_id} updated successfully.")
            return redirect('task_list')

        except Exception as e:
            messages.error(request, f"Error updating task: {str(e)}")

    # GET request — prefill form with existing task data
    employees = Employee.objects.all().order_by('employee_name')
    customers = Lead.objects.all().order_by('customer_name')
    services = Service.objects.all().order_by('name')

    context = {
        'task': task,
        'employees': employees,
        'customers': customers,
        'services': services,
    }
    return render(request, 'edit_task.html', context)

def task_detail(request, task_id):
    """Return task details as JSON"""
    task = get_object_or_404(Task, id=task_id)

    data = {
        'task_id': task.task_id,
        'assigned_to': task.assigned_to.employee_name,
        'customer_name': task.customer_name.customer_name,
        'service_name': task.service_name.name,
        'delivery_date': task.delivery_date.strftime('%Y-%m-%d'),
        'payment_amount': float(task.payment_amount),
        'payment_status': task.payment_status,
        'balance_amount': float(task.balance_amount) if task.balance_amount else 0,
        'task_notes': task.task_notes or '',
        'task_status': task.task_status,
        'created_at': task.created_at.strftime('%d %B, %Y'),
        'is_overdue': task.is_overdue,
    }

    return JsonResponse(data)

@require_POST
@csrf_exempt
def delete_task(request, task_id):
    try:
        task = get_object_or_404(Task, id=task_id)
        task_id_str = task.task_id

        task.delete()

        messages.success(request, f'Task "{task_id_str}" deleted successfully!')
        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_POST
@csrf_exempt
def update_task_status(request, task_id):
    try:
        task = get_object_or_404(Task, id=task_id)
        new_status = request.POST.get('status')
        
        if new_status in dict(Task.TASK_STATUS_CHOICES):
            task.task_status = new_status
            task.save()
            
            messages.success(request, f'Task {task.task_id} status updated to {new_status.title()}!')
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    

# def payment_list(request):
#     """Display all payments with filtering and search functionality"""
    
#     # Get filter parameters
#     status_filter = request.GET.get('status', '')
#     employee_filter = request.GET.get('employee', '')
#     service_filter = request.GET.get('service', '')
#     search_query = request.GET.get('search', '')
    
#     # Base queryset - get all tasks as they contain payment information
#     payments = Task.objects.all().select_related('customer_name', 'assigned_to', 'service_name')
    
#     # Apply filters
#     if status_filter:
#         payments = payments.filter(payment_status=status_filter)
    
#     if employee_filter:
#         payments = payments.filter(assigned_to_id=employee_filter)
    
#     if service_filter:
#         payments = payments.filter(service_name_id=service_filter)
    
#     if search_query:
#         payments = payments.filter(
#             Q(customer_name__customer_name__icontains=search_query) |
#             Q(task_id__icontains=search_query) |
#             Q(service_name__name__icontains=search_query) |
#             Q(assigned_to__employee_name__icontains=search_query)
#         )
    
#     # Order by creation date (newest first)
#     payments = payments.order_by('-created_at')
    
#     # Pagination
#     paginator = Paginator(payments, 15)  # Show 15 payments per page
#     page_number = request.GET.get('page')
#     payments = paginator.get_page(page_number)
    
#     # Calculate statistics
#     all_payments = Task.objects.all()
#     total_payments = all_payments.count()
#     paid_payments = all_payments.filter(payment_status='paid').count()
#     pending_payments = all_payments.filter(payment_status='pending').count()
#     partial_payments = all_payments.filter(payment_status='partial').count()
    
#     # Calculate amounts
#     total_amount = all_payments.aggregate(Sum('payment_amount'))['payment_amount__sum'] or 0
#     paid_amount = all_payments.filter(payment_status='paid').aggregate(Sum('payment_amount'))['payment_amount__sum'] or 0
#     pending_amount = all_payments.filter(payment_status='pending').aggregate(Sum('payment_amount'))['payment_amount__sum'] or 0
#     balance_amount = all_payments.aggregate(Sum('balance_amount'))['balance_amount__sum'] or 0
    
#     # Get all employees and services for filter dropdowns
#     employees = Employee.objects.all().order_by('employee_name')
#     services = Service.objects.all().order_by('name')
    
#     context = {
#         'payments': payments,
#         'total_payments': total_payments,
#         'paid_payments': paid_payments,
#         'pending_payments': pending_payments,
#         'partial_payments': partial_payments,
#         'total_amount': total_amount,
#         'paid_amount': paid_amount,
#         'pending_amount': pending_amount,
#         'balance_amount': balance_amount,
#         'employees': employees,
#         'services': services,
#         'status_filter': status_filter,
#         'employee_filter': employee_filter,
#         'service_filter': service_filter,
#         'search_query': search_query,
#     }
    
#     return render(request, 'payment_list.html', context)

def payment_list(request):
    """
    Display all payments with filters & pagination,
    pass payment amounts and calculate % paid for coloring rows.
    """
    # Filters from GET parameters
    status_filter = request.GET.get('status', '')
    employee_filter = request.GET.get('employee', '')
    service_filter = request.GET.get('service', '')
    search_query = request.GET.get('search', '')

    # Base queryset - use select_related for performance
    payments_qs = Task.objects.all().select_related('customer_name', 'assigned_to', 'service_name')

    # Apply filters
    if status_filter:
        payments_qs = payments_qs.filter(payment_status=status_filter)

    if employee_filter:
        payments_qs = payments_qs.filter(assigned_to_id=employee_filter)

    if service_filter:
        payments_qs = payments_qs.filter(service_name_id=service_filter)

    if search_query:
        payments_qs = payments_qs.filter(
            Q(customer_name__customer_name__icontains=search_query) |
            Q(task_id__icontains=search_query) |
            Q(service_name__name__icontains=search_query) |
            Q(assigned_to__employee_name__icontains=search_query)
        )

    # Order by newest first
    payments_qs = payments_qs.order_by('-created_at')

    # Paginate (15 per page, you can adjust)
    paginator = Paginator(payments_qs, 10)
    page_number = request.GET.get('page')
    payments_page = paginator.get_page(page_number)

    # Calculate percent_paid for display/coloring
    for payment in payments_page:
        if payment.payment_amount and payment.amount_paid is not None:
            payment.percent_paid = min(100, (payment.amount_paid / payment.payment_amount) * 100)
        else:
            payment.percent_paid = 0

    # Aggregate statistics for dashboard cards
    all_payments = Task.objects.all()
    total_payments = all_payments.count()
    paid_payments = all_payments.filter(payment_status='paid').count()
    pending_payments = all_payments.filter(payment_status='pending').count()
    partial_payments = all_payments.filter(payment_status='partial').count()

    total_amount = all_payments.aggregate(Sum('payment_amount'))['payment_amount__sum'] or 0
    paid_amount = all_payments.filter(payment_status='paid').aggregate(Sum('payment_amount'))['payment_amount__sum'] or 0
    pending_amount = all_payments.filter(payment_status='pending').aggregate(Sum('payment_amount'))['payment_amount__sum'] or 0
    balance_amount = all_payments.aggregate(Sum('balance_amount'))['balance_amount__sum'] or 0

    employees = Employee.objects.all().order_by('employee_name')
    services = Service.objects.all().order_by('name')

    context = {
        'payments': payments_page,
        'total_payments': total_payments,
        'paid_payments': paid_payments,
        'pending_payments': pending_payments,
        'partial_payments': partial_payments,
        'total_amount': total_amount,
        'paid_amount': paid_amount,
        'pending_amount': pending_amount,
        'balance_amount': balance_amount,
        'employees': employees,
        'services': services,
        'status_filter': status_filter,
        'employee_filter': employee_filter,
        'service_filter': service_filter,
        'search_query': search_query,
    }
    return render(request, 'payment_list.html', context)


def payment_detail(request, payment_id):
    """
    AJAX endpoint to get payment details in JSON for edit modal.
    """
    try:
        payment = get_object_or_404(Task, id=payment_id)

        data = {
            'task_id': payment.task_id,
            'customer_name': payment.customer_name.customer_name,
            'customer_phone': payment.customer_name.customer_phone,
            'customer_email': payment.customer_name.customer_email,
            'assigned_to': payment.assigned_to.employee_name,
            'service_name': payment.service_name.name,
            'payment_amount': float(payment.payment_amount or 0),
            'amount_paid': float(payment.amount_paid or 0),
            'balance_amount': float(payment.balance_amount or 0),
            'payment_status': payment.payment_status,  # Use the code value ('paid', 'partial', etc.)
            'payment_status_display': payment.get_payment_status_display(),
            'delivery_date': payment.delivery_date.strftime('%Y-%m-%d') if payment.delivery_date else '',
            'task_status': payment.get_task_status_display(),
            'task_notes': payment.task_notes or 'No notes available',
            'created_at': payment.created_at.strftime('%d %b, %Y at %I:%M %p'),
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def update_payment_status(request, payment_id):
    """
    AJAX endpoint to update payment status and amount paid.
    Expects JSON body with keys 'payment_status' and optionally 'amount_paid'.
    """
    if request.method == 'POST':
        try:
            payment = get_object_or_404(Task, id=payment_id)
            data = json.loads(request.body.decode('utf-8'))

            new_status = data.get('payment_status')
            new_amount_paid = data.get('amount_paid')

            if new_status not in ['paid', 'pending', 'partial']:
                return JsonResponse({'success': False, 'error': 'Invalid payment status'})

            payment.payment_status = new_status

            # Validate and update amount_paid and balance_amount
            if new_amount_paid is not None:
                try:
                    amount_paid_val = float(new_amount_paid)
                    if amount_paid_val < 0:
                        return JsonResponse({'success': False, 'error': 'Amount paid cannot be negative'})

                    if amount_paid_val > payment.payment_amount:
                        return JsonResponse({'success': False, 'error': 'Amount paid cannot exceed total payment amount'})

                    payment.amount_paid = amount_paid_val
                    payment.balance_amount = payment.payment_amount - amount_paid_val
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Invalid amount paid value'})
            else:
                # If no amount_paid given, adjust amount_paid based on status
                if new_status == 'paid':
                    payment.amount_paid = payment.payment_amount
                    payment.balance_amount = 0
                elif new_status == 'pending':
                    payment.amount_paid = 0
                    payment.balance_amount = payment.payment_amount
                # For partial, amount_paid should be provided

            payment.save()
            messages.success(request, f'Payment status updated to {payment.get_payment_status_display()}')
            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # For any non-POST requests:
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def payment_view(request, payment_id):
    """Display full details of a payment specified by payment_id"""
    payment = get_object_or_404(Task, id=payment_id)

    context = {
        'payment': payment,
    }

    return render(request, 'payment_view.html', context)

def payment_receipt(request, payment_id):
    payment = get_object_or_404(Task, id=payment_id)
    # Render a template showing the receipt details formatted for printing
    return render(request, 'payment_receipt.html', {'payment': payment})

def edit_payment(request, payment_id):
    """
    Display a form to edit payment details (payment_status and amount_paid) of a Task,
    and process updates.
    """
    task = get_object_or_404(Task, id=payment_id)

    if request.method == 'POST':
        payment_status = request.POST.get('payment_status')
        amount_paid_raw = request.POST.get('amount_paid', '0')

        # Validate payment_status
        if payment_status not in dict(Task.PAYMENT_STATUS_CHOICES).keys():
            messages.error(request, "Invalid payment status selected.")
            return redirect('edit_payment', payment_id=payment_id)

        try:
            amount_paid = Decimal(amount_paid_raw)
            if amount_paid < 0:
                raise ValueError("Amount paid cannot be negative.")
            if amount_paid > task.payment_amount:
                raise ValueError("Amount paid cannot exceed total payment amount.")
        except Exception as e:
            messages.error(request, f"Invalid amount paid: {e}")
            return redirect('edit_payment', payment_id=payment_id)

        # Set amount_paid to 0 automatically if status is 'pending'
        if payment_status == 'pending':
            amount_paid = Decimal('0.00')

        # Calculate balance
        balance = max(task.payment_amount - amount_paid, Decimal('0.00'))

        # Update fields atomically
        try:
            with transaction.atomic():
                task.payment_status = payment_status
                task.amount_paid = amount_paid
                task.balance_amount = balance
                task.save()
            messages.success(request, f"Payment updated successfully for Task {task.task_id}.")
            return redirect('payment_view', payment_id=task.id)
        except Exception as e:
            messages.error(request, f"Error saving payment: {e}")
            return redirect('edit_payment', payment_id=payment_id)

    # For GET request, render the form
    return render(request, 'edit_payment.html', {
        'payment': task,
    })


def all_leads(request):
    """Display all leads with search and pagination functionality"""
    # Get search query from request
    search_query = request.GET.get('search', '')
    
    # Base queryset
    leads = Lead.objects.filter(lead_type='lead')
    
    # Apply search filter if search query exists
    if search_query:
        leads = leads.filter(
            Q(customer_name__icontains=search_query) |
            Q(customer_id__icontains=search_query) |
            Q(mobile_no__icontains=search_query) |
            Q(email_id__icontains=search_query) |
            Q(company_name__icontains=search_query)
        )
    leads=leads.order_by('-created_at')
    # Get total count for display
    total_leads = leads.count()
    
    # Pagination
    paginator = Paginator(leads, 3)  # Show 10 leads per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'leads': page_obj,
        'search_query': search_query,
        'total_leads': total_leads,
        'page_obj': page_obj,
    }
    
    return render(request, 'all_leads.html', context)

def view_lead(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    services = LeadService.objects.filter(lead=lead)

    return render(request, 'view_lead.html', {
        'lead': lead,
        'services': services,
    })



def edit_lead(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id, lead_type='lead')
    
    if request.method == 'POST':
        # update fields from POST data
        lead.customer_id = request.POST.get('customer_id')
        lead.customer_name = request.POST.get('customer_name')
        lead.mobile_no = request.POST.get('mobile_no')
        lead.father_name = request.POST.get('father_name')
        lead.spouse_name = request.POST.get('spouse_name')
        lead.mother_name = request.POST.get('mother_name')
        lead.aadhar_card_no = request.POST.get('aadhar_card_no')
        lead.pan_no = request.POST.get('pan_no')
        lead.company_name = request.POST.get('company_name')
        lead.email_id = request.POST.get('email_id')
        lead.gst_no = request.POST.get('gst_no')
        lead.cin_no = request.POST.get('cin_no')
        lead.assigned_to = request.POST.get('assigned_to')
        lead.delivery_date = request.POST.get('delivery_date') or None
        lead.note = request.POST.get('note')

        if 'upload_document' in request.FILES:
            lead.upload_document = request.FILES['upload_document']

        
        if 'delete_document' in request.POST:
            if lead.upload_document:
                lead.upload_document.delete(save=False)  # delete file from media folder
                lead.upload_document = None
                lead.document_name = None
                lead.save()
                messages.success(request, "Document removed successfully.")
            return redirect('edit_lead', lead_id=lead.id)

        lead.save()

        # Update services
        selected_services_json = request.POST.get('selected_services', '[]')
        if selected_services_json and selected_services_json != '[]':
            LeadService.objects.filter(lead=lead).delete()
            try:
                services_data = json.loads(selected_services_json)
                for service_data in services_data:
                    service_obj = Service.objects.get(id=service_data['id'])
                    LeadService.objects.create(
                        lead=lead,
                        service=service_obj,
                        service_price=service_data['price']
                    )
            except json.JSONDecodeError:
                messages.error(request, "Invalid services data.")

        messages.success(request, f'Lead "{lead.customer_name}" updated successfully!')
        return redirect('all_leads')
    
    # GET request
    current_services = LeadService.objects.filter(lead=lead).select_related('service')
    selected_services = [
        {
            'id': svc.service.id,
            'name': svc.service.name,
            'price': float(svc.service_price)
        } for svc in current_services
    ]
    services = Service.objects.all()
    context = {
        'lead': lead,
        'services': services,
        'current_services': json.dumps(selected_services),
    }
    return render(request, 'edit_lead.html', context)



# def delete_lead(request, lead_id):
#     lead = get_object_or_404(Lead, pk=lead_id, lead_type='lead')
#     lead_name = lead.customer_name
#     lead.delete()
#     messages.success(request, f'Lead "{lead_name}" has been deleted successfully!')
#     return redirect('delete')

@require_http_methods(["GET","POST"])
def delete_lead(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id, lead_type='lead')

    if request.method == 'POST':
        lead.lead_type = 'customer'
        lead.delete()
        messages.success(request, f'Lead "{lead.customer_name}" has been deleted successfully!')
        return redirect('all_leads')

    # GET: render confirmation page
    return render(request, 'delete_lead.html', {'lead': lead})

@require_http_methods(["GET","POST"])
def convert_to_customer(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id, lead_type='lead')

    if request.method == 'POST':
        lead.lead_type = 'customer'
        lead.save()
        messages.success(request, f'Lead "{lead.customer_name}" has been converted to a Customer successfully!')
        return redirect('all_leads')

    # GET: render confirmation page
    return render(request, 'convert_to_customer.html', {'lead': lead})

