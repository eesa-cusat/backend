from django.contrib import admin
from django.http import HttpResponse
from django.urls import path
from django.utils.html import format_html
from django.db.models import Count
from django.shortcuts import render, redirect
from django.contrib import messages
import csv
import io
from .models import Alumni


@admin.register(Alumni)
class AlumniAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'email', 'year_of_passout', 'employment_status', 
        'current_company', 'is_verified', 'is_active', 'created_at'
    ]
    list_filter = [
        'year_of_passout', 'employment_status', 'is_verified', 
        'is_active', 'willing_to_mentor', 'created_at'
    ]
    search_fields = [
        'full_name', 'email', 'student_id', 'current_company',
        'job_title'
    ]
    readonly_fields = [
        'id', 'department', 'years_since_graduation', 'batch_name',
        'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'full_name', 'email', 'phone_number', 'alternative_phone'
            )
        }),
        ('Academic Information', {
            'fields': (
                'student_id', 'scheme', 'year_of_joining', 'year_of_passout',
                'department', 'specialization', 'cgpa'
            )
        }),
        ('Current Status', {
            'fields': (
                'employment_status', 'job_title', 'current_company',
                'current_location', 'linkedin_profile'
            )
        }),
        ('Additional Information', {
            'fields': ('achievements', 'feedback'),
            'classes': ('collapse',)
        }),
        ('Contact Preferences', {
            'fields': (
                'willing_to_mentor', 'allow_contact_from_juniors',
                'newsletter_subscription'
            )
        }),
        ('Status', {
            'fields': ('is_verified', 'is_active')
        }),
        ('Metadata', {
            'fields': (
                'id', 'years_since_graduation', 'batch_name',
                'created_by', 'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_verified', 'mark_as_unverified', 'export_as_csv']
    
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} alumni marked as verified.')
    mark_as_verified.short_description = "Mark selected alumni as verified"
    
    def mark_as_unverified(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} alumni marked as unverified.')
    mark_as_unverified.short_description = "Mark selected alumni as unverified"
    
    def export_as_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="alumni_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Full Name', 'Email', 'Phone', 'Year of Passout',
            'Department', 'Current Company', 'Job Title',
            'Employment Status', 'LinkedIn', 'Willing to Mentor', 'Is Verified'
        ])
        
        for alumni in queryset:
            writer.writerow([
                alumni.full_name, alumni.email, alumni.phone_number,
                alumni.year_of_passout, alumni.department,
                alumni.current_company, alumni.job_title,
                alumni.employment_status, alumni.linkedin_profile,
                alumni.willing_to_mentor, alumni.is_verified
            ])
        
        return response
    export_as_csv.short_description = "Export selected alumni as CSV"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')
    
    def get_urls(self):
        """Add custom URL for CSV upload"""
        urls = super().get_urls()
        custom_urls = [
            path('upload-csv/', self.admin_site.admin_view(self.upload_csv), name='alumni_upload_csv'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        """Add CSV upload button to changelist"""
        extra_context = extra_context or {}
        extra_context['csv_upload_url'] = 'upload-csv/'
        return super().changelist_view(request, extra_context=extra_context)
    
    def upload_csv(self, request):
        """Handle CSV upload"""
        if request.method == 'POST' and 'csv_file' in request.FILES:
            csv_file = request.FILES['csv_file']
            
            try:
                # Read CSV file
                decoded_file = csv_file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)
                
                # Expected headers
                required_headers = ['full_name', 'email', 'year_of_passout']
                optional_headers = [
                    'phone_number', 'student_id', 'scheme', 'year_of_joining',
                    'specialization', 'cgpa', 'job_title', 'current_company',
                    'current_location', 'employment_status', 'linkedin_profile'
                ]
                
                # Validate headers
                csv_headers = reader.fieldnames or []
                missing_headers = [h for h in required_headers if h not in csv_headers]
                if missing_headers:
                    messages.error(request, f'Missing required headers: {", ".join(missing_headers)}')
                    return redirect('..')
                
                # Process rows
                successful_imports = 0
                failed_imports = 0
                error_log = []
                
                for row_num, row in enumerate(reader, start=1):
                    try:
                        # Clean and prepare data
                        alumni_data = {
                            'full_name': row.get('full_name', '').strip(),
                            'email': row.get('email', '').strip(),
                            'year_of_passout': int(row.get('year_of_passout', 0))
                        }
                        
                        # Add optional fields
                        for header in optional_headers:
                            if header in row and row[header].strip():
                                value = row[header].strip()
                                if header in ['year_of_joining', 'scheme']:
                                    alumni_data[header] = int(value) if value else None
                                elif header == 'cgpa':
                                    alumni_data[header] = float(value) if value else None
                                else:
                                    alumni_data[header] = value
                        
                        # Set defaults
                        if 'scheme' not in alumni_data and 'year_of_joining' in alumni_data:
                            alumni_data['scheme'] = alumni_data['year_of_joining']
                        if 'year_of_joining' not in alumni_data:
                            alumni_data['year_of_joining'] = alumni_data['year_of_passout'] - 4
                        
                        # Create alumni record
                        Alumni.objects.create(created_by=request.user, **alumni_data)
                        successful_imports += 1
                        
                    except Exception as e:
                        failed_imports += 1
                        error_log.append(f"Row {row_num}: {str(e)}")
                
                if successful_imports > 0:
                    messages.success(request, f'Successfully imported {successful_imports} alumni records.')
                if failed_imports > 0:
                    messages.warning(request, f'{failed_imports} records failed. First few errors: {"; ".join(error_log[:3])}')
                
                return redirect('..')
                
            except Exception as e:
                messages.error(request, f'Error processing CSV file: {str(e)}')
                return redirect('..')
        
        # Show upload form
        context = {
            'title': 'Upload Alumni CSV',
            'opts': self.model._meta,
        }
        return render(request, 'admin/alumni/upload_csv.html', context)
