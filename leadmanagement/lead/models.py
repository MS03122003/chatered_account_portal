from django.db import models
from django.contrib.auth.models import User
import os
from decimal import Decimal


class Employee(models.Model):
    employee_id = models.CharField(max_length=20, unique=True)
    employee_name = models.CharField(max_length=100)
    designation = models.CharField(max_length=60,default="none")
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()

    def __str__(self):
        return f"{self.employee_name} ({self.employee_id})"

class Service(models.Model):
    CATEGORY_CHOICES = [
        ('Tax', 'Tax'),
        ('Registration', 'Registration'),
        ('Consultancy', 'Consultancy'),
        ('Filing', 'Filing'),
        ('Legal', 'Legal'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Lead(models.Model):
    LEAD_TYPE_CHOICES = [
    ('customer', 'Customer'),
    ('partner', 'Partner'),
    ('vendor', 'Vendor'),
    ('other', 'Other'),
]
    customer_id = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=200)
    mobile_no = models.CharField(max_length=15)
    father_name = models.CharField(max_length=200, blank=True, null=True)
    spouse_name = models.CharField(max_length=200, blank=True, null=True)
    mother_name = models.CharField(max_length=200, blank=True, null=True)
    aadhar_card_no = models.CharField(max_length=12, blank=True, null=True)
    pan_no = models.CharField(max_length=10, blank=True, null=True)
    company_name = models.CharField(max_length=200, blank=True, null=True)
    email_id = models.EmailField(blank=True, null=True)
    gst_no = models.CharField(max_length=15, blank=True, null=True)
    cin_no = models.CharField(max_length=21, blank=True, null=True)
    assigned_to = models.CharField(max_length=200, blank=True, null=True)
    delivery_date = models.DateField(blank=True, null=True)
    document_name = models.CharField(max_length=255, blank=True, null=True)  # Add this line
    upload_document = models.FileField(upload_to='documents', blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    lead_type = models.CharField(max_length=10, choices=LEAD_TYPE_CHOICES, default='lead')

    
    
    def __str__(self):
        return f"{self.customer_name} - {self.customer_id}"
    
    class Meta:
        ordering = ['-created_at']

def lead_document_upload_path(instance, filename):
    """Generate upload path for lead documents"""
    # Get file extension
    ext = filename.split('.')[-1]
    # Create new filename: customer_id_original_name.ext
    new_filename = f"{instance.customer_id}_{filename}"
    # Return the full path: documents/customer_id_filename.ext
    return os.path.join('documents', new_filename)

class LeadService(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='services')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    service_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.lead.customer_name} - {self.service.name}"
    
    class Meta:
        unique_together = ['lead', 'service']

class Task(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('partial', 'Partial Paid'),
    ]
    
    TASK_STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]
    
    task_id = models.CharField(max_length=20, unique=True, blank=True)
    assigned_to = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='assigned_tasks')
    customer_name = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='customer_tasks')
    service_name = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='service_tasks')
    delivery_date = models.DateField()

    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)

    task_notes = models.TextField(blank=True, null=True)
    task_status = models.CharField(max_length=15, choices=TASK_STATUS_CHOICES, default='assigned')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Generate task ID
        if not self.task_id:
            last_task = Task.objects.order_by('-id').first()
            new_number = int(last_task.task_id[3:]) + 1 if last_task else 1
            self.task_id = f"TSK{new_number:03d}"

        # Auto calculate balance based on payment status and amount paid
        if self.payment_status == 'paid':
            self.amount_paid = self.payment_amount
            self.balance_amount = Decimal('0.00')
        elif self.payment_status == 'pending':
            self.amount_paid = Decimal('0.00')
            self.balance_amount = self.payment_amount
        elif self.payment_status == 'partial':
            self.balance_amount = max(self.payment_amount - self.amount_paid, Decimal('0.00'))

        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.task_id} - {self.customer_name.customer_name} - {self.service_name.name}"