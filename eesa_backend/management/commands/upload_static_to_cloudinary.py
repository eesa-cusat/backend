from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.staticfiles.finders import find
import cloudinary.uploader
import os

class Command(BaseCommand):
    help = 'Upload static files to Cloudinary'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing static files from Cloudinary before upload',
        )

    def handle(self, *args, **options):
        if settings.DEBUG:
            self.stdout.write("This command should be run in production mode (DEBUG=False)")
            return
        
        self.stdout.write("=== Uploading Static Files to Cloudinary ===")
        
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )
        
        # Clear existing files if requested
        if options['clear']:
            self.stdout.write("Clearing existing static files from Cloudinary...")
            try:
                result = cloudinary.api.resources(
                    type='upload',
                    resource_type='raw',
                    prefix='static/',
                    max_results=500
                )
                
                static_files = result.get('resources', [])
                if static_files:
                    public_ids = [resource['public_id'] for resource in static_files]
                    cloudinary.api.delete_resources(public_ids, resource_type='raw')
                    self.stdout.write(f"Deleted {len(static_files)} existing files")
                else:
                    self.stdout.write("No existing files to delete")
            except Exception as e:
                self.stdout.write(f"Error clearing files: {e}")
        
        # List of important static files to upload
        static_files = [
            # Admin CSS files
            'admin/css/base.css',
            'admin/css/dashboard.css',
            'admin/css/forms.css',
            'admin/css/changelists.css',
            'admin/css/login.css',
            'admin/css/nav_sidebar.css',
            'admin/css/responsive.css',
            'admin/css/autocomplete.css',
            'admin/css/widgets.css',
            'admin/css/dark_mode.css',
            'admin/css/rtl.css',
            'admin/css/responsive_rtl.css',
            'admin/css/unusable_password_field.css',
            
            # Admin JavaScript files
            'admin/js/core.js',
            'admin/js/actions.js',
            'admin/js/calendar.js',
            'admin/js/cancel.js',
            'admin/js/change_form.js',
            'admin/js/filters.js',
            'admin/js/inlines.js',
            'admin/js/jquery.init.js',
            'admin/js/nav_sidebar.js',
            'admin/js/popup_response.js',
            'admin/js/prepopulate_init.js',
            'admin/js/prepopulate.js',
            'admin/js/SelectBox.js',
            'admin/js/SelectFilter2.js',
            'admin/js/theme.js',
            'admin/js/urlify.js',
            'admin/js/unusable_password_field.js',
            'admin/js/admin/DateTimeShortcuts.js',
            'admin/js/admin/RelatedObjectLookups.js',
            
            # Admin images
            'admin/img/icon-addlink.svg',
            'admin/img/icon-deletelink.svg',
            'admin/img/icon-changelink.svg',
            'admin/img/icon-viewlink.svg',
            'admin/img/icon-yes.svg',
            'admin/img/icon-no.svg',
            'admin/img/icon-unknown.svg',
            'admin/img/icon-unknown-alt.svg',
            'admin/img/icon-alert.svg',
            'admin/img/icon-calendar.svg',
            'admin/img/icon-clock.svg',
            'admin/img/icon-hidelink.svg',
            'admin/img/search.svg',
            'admin/img/selector-icons.svg',
            'admin/img/sorting-icons.svg',
            'admin/img/calendar-icons.svg',
            'admin/img/tooltag-add.svg',
            'admin/img/tooltag-arrowright.svg',
            'admin/img/inline-delete.svg',
        ]
        
        self.stdout.write(f"Uploading {len(static_files)} static files to Cloudinary...")
        
        uploaded_count = 0
        failed_count = 0
        
        for static_file in static_files:
            try:
                # Find the file
                file_path = find(static_file)
                if not file_path or not os.path.exists(file_path):
                    self.stdout.write(f"❌ {static_file} - File not found")
                    failed_count += 1
                    continue
                
                # Create the public_id with static prefix for organization
                # In Dynamic folders mode, this provides logical organization
                public_id = f"static/{static_file}"
                
                self.stdout.write(f"📤 Uploading: {static_file}")
                
                # Upload to Cloudinary
                result = cloudinary.uploader.upload(
                    file_path,
                    public_id=public_id,
                    resource_type='raw',
                    overwrite=True
                )
                
                uploaded_count += 1
                self.stdout.write(f"   ✅ Uploaded: {result.get('public_id')}")
                
            except Exception as e:
                failed_count += 1
                self.stdout.write(f"   ❌ Failed: {e}")
        
        self.stdout.write("")
        self.stdout.write(f"Upload Summary:")
        self.stdout.write(f"   ✅ Successfully uploaded: {uploaded_count}")
        self.stdout.write(f"   ❌ Failed uploads: {failed_count}")
        self.stdout.write(f"   📊 Total files: {len(static_files)}")
        
        # Verify uploads
        self.stdout.write("")
        self.stdout.write("Verifying uploads...")
        try:
            result = cloudinary.api.resources(
                type='upload',
                resource_type='raw',
                prefix='static/',
                max_results=50
            )
            
            cloudinary_files = result.get('resources', [])
            self.stdout.write(f"Files with static prefix: {len(cloudinary_files)}")
            
        except Exception as e:
            self.stdout.write(f"Error verifying uploads: {e}")
        
        self.stdout.write("✅ Static files upload completed!") 