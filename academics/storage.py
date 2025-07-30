from django.conf import settings

# Import Cloudinary storage classes
try:
    from cloudinary_storage.storage import MediaCloudinaryStorage
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False

# Define the storage class (always available for migrations)
if CLOUDINARY_AVAILABLE:
    class PDFCloudinaryStorage(MediaCloudinaryStorage):
        """
        Custom Cloudinary storage for PDF files to ensure proper resource type
        and settings for browser preview.
        """
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Set resource type to 'raw' to ensure PDFs are not treated as images
            self.resource_type = 'raw'
        
        def _save(self, name, content):
            """
            Override save method to ensure PDFs are uploaded correctly
            """
            # Check if this is a PDF file by content type or name
            is_pdf = (
                name.lower().endswith('.pdf') or 
                hasattr(content, 'content_type') and content.content_type == 'application/pdf' or
                hasattr(content, 'name') and content.name.lower().endswith('.pdf')
            )
            
            if is_pdf:
                try:
                    # Read the content
                    content.seek(0)
                    file_content = content.read()
                    
                    # Clean the name to avoid double extensions
                    clean_name = name.replace('.pdf', '') if name.endswith('.pdf') else name
                    
                    # Upload to Cloudinary with raw resource type to ensure PDFs are not treated as images
                    result = cloudinary.uploader.upload(
                        file_content,
                        public_id=clean_name,
                        resource_type='raw',
                        format='pdf'
                    )
                    
                    # Return the public_id with .pdf extension for auto resource type
                    public_id = result['public_id']
                    if not public_id.endswith('.pdf'):
                        return f"{public_id}.pdf"
                    return public_id
                    
                except Exception as e:
                    # Fallback to parent method if direct upload fails
                    return super()._save(name, content)
            else:
                # For non-PDF files, use parent method
                return super()._save(name, content)
        
        def url(self, name):
            """
            Override URL method to ensure proper PDF URLs
            """
            # If the name is already a full URL, return it directly
            if name.startswith('http'):
                return name
            
            url = super().url(name)
            
            # Ensure PDF URLs are properly formatted
            if name.lower().endswith('.pdf'):
                # For raw resource type, ensure we're using the correct URL format
                if 'res.cloudinary.com' in url:
                    # Make sure we're using raw upload URLs for PDFs
                    if '/image/upload/' in url:
                        url = url.replace('/image/upload/', '/raw/upload/')
                    return url
            
            return url 