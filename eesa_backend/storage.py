from django.conf import settings

# Import Cloudinary storage classes
try:
    from cloudinary_storage.storage import StaticHashedCloudinaryStorage
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False

if CLOUDINARY_AVAILABLE:
    class CustomStaticHashedCloudinaryStorage(StaticHashedCloudinaryStorage):
        """
        Custom static files storage for Cloudinary with proper folder organization
        """
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Ensure static files are organized properly
            self.location = 'static'
        
        def url(self, name):
            """
            Override URL method to ensure proper static file URLs
            """
            # Ensure the name has the static prefix
            if not name.startswith('static/'):
                name = f'static/{name}'
            
            return super().url(name)
        
        def _save(self, name, content):
            """
            Override save method to ensure proper folder structure
            """
            # Ensure the name has the static prefix
            if not name.startswith('static/'):
                name = f'static/{name}'
            
            return super()._save(name, content) 