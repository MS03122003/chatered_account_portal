from django.db import models
from django.contrib.auth.models import User

class Employee(models.Model):
    employee_id = models.CharField(max_length=20, unique=True)
    employee_name = models.CharField(max_length=100)
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
    upload_document = models.FileField(upload_to='documents/', blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.customer_name} - {self.customer_id}"
    
    class Meta:
        ordering = ['-created_at']

class LeadService(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='services')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    service_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.lead.customer_name} - {self.service.name}"
    
    class Meta:
        unique_together = ['lead', 'service']

