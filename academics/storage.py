from django.conf import settings

try:
    from cloudinary_storage.storage import MediaCloudinaryStorage
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False

if CLOUDINARY_AVAILABLE:
    class PDFCloudinaryStorage(MediaCloudinaryStorage):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.resource_type = 'raw'
        
        def _save(self, name, content):
            is_pdf = name.lower().endswith('.pdf')
            
            if is_pdf:
                try:
                    content.seek(0)
                    file_content = content.read()
                    clean_name = name.replace('.pdf', '') if name.endswith('.pdf') else name
                    
                    result = cloudinary.uploader.upload(
                        file_content,
                        public_id=clean_name,
                        resource_type='raw',
                        format='pdf',
                        overwrite=True,
                        use_filename=False,
                        unique_filename=False,
                    )
                    
                    public_id = result['public_id']
                    return f"{public_id}.pdf" if not public_id.endswith('.pdf') else public_id
                    
                except Exception:
                    return super()._save(name, content)
            else:
                return super()._save(name, content)
        
        def url(self, name):
            if name.startswith('http'):
                return name
            
            url = super().url(name)
            
            if name.lower().endswith('.pdf') and 'res.cloudinary.com' in url:
                if '/image/upload/' in url:
                    url = url.replace('/image/upload/', '/raw/upload/')
                if '?' not in url:
                    url += '?fl_attachment'
                elif 'fl_attachment' not in url:
                    url += '&fl_attachment'
            
            return url

else:
    class PDFCloudinaryStorage:
        def __init__(self, *args, **kwargs):
            from django.core.files.storage import FileSystemStorage
            self._storage = FileSystemStorage(*args, **kwargs)
        
        def __getattr__(self, name):
            return getattr(self._storage, name)
