from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout



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

# New Leads view
def new_lead(request):
    return render(request, 'new_lead.html')

# Customer view
def customer(request):
    return render(request, 'customer.html')

# Add Services view
def add_services(request):
    return render(request, 'add_services.html')

def add_employee(request):
    return render(request, 'add_employee.html') 

# Logout view (POST method preferred for logout)
def logout_view(request):
    if request.method == 'POST':
        auth_logout(request)
        return redirect('login')  # change 'login' to your login page url name
    return redirect('dashboard')
