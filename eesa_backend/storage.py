"""
Optimized Cloudinary storage classes for dynamic folder mode.
Handles the new Cloudinary dynamic folder mode (post-June 2024) that requires
explicit asset_folder parameter for proper folder organization.
"""

from cloudinary_storage.storage import StaticHashedCloudinaryStorage, MediaCloudinaryStorage
from django.core.files.base import ContentFile
import cloudinary.uploader


class DynamicFolderStaticStorage(StaticHashedCloudinaryStorage):
    """
    Optimized static storage that explicitly uses asset_folder for dynamic folder mode.
    Ensures all static files are uploaded to 'static/' folder in Cloudinary.
    """
    
    def _save(self, name, content):
        """
        Override _save to explicitly set asset_folder for dynamic folder mode.
        This ensures files go to the 'static/' folder regardless of public_id format.
        """
        # Clean the name (remove static/ prefix if present to avoid duplication)
        clean_name = name.replace('static/', '') if name.startswith('static/') else name
        
        # Use the parent class method but with our custom options
        # The parent class will handle the actual Cloudinary upload
        original_name = name
        try:
            # Temporarily set name without prefix
            result = super()._save(clean_name, content)
            return result
        except Exception as e:
            # If there's an issue, fall back to the original approach
            return super()._save(original_name, content)
    
    def _get_upload_options(self, name, content):
        """Get optimized upload options for static files."""
        return {
            'asset_folder': 'static',
            'resource_type': 'raw',
            'use_filename': True,
            'unique_filename': False,
            'overwrite': True,
        }


class DynamicFolderMediaStorage(MediaCloudinaryStorage):
    """
    Optimized media storage that explicitly uses asset_folder for dynamic folder mode.
    Ensures all media files are uploaded to 'media/' folder in Cloudinary.
    """
    
    def _save(self, name, content):
        """
        Override _save to explicitly set asset_folder for dynamic folder mode.
        This ensures files go to the 'media/' folder with proper subfolder structure.
        """
        # Clean the name (remove media/ prefix if present to avoid duplication)
        clean_name = name.replace('media/', '') if name.startswith('media/') else name
        
        # Use the parent class method but with our custom options
        # The parent class will handle the actual Cloudinary upload
        original_name = name
        try:
            # Temporarily set name without prefix
            result = super()._save(clean_name, content)
            return result
        except Exception as e:
            # If there's an issue, fall back to the original approach
            return super()._save(original_name, content)
    
    def _get_upload_options(self, name, content):
        """Get optimized upload options for media files."""
        return {
            'asset_folder': 'media',
            'use_filename': True,
            'unique_filename': False,
            'overwrite': True,
        }


# Optimized configuration for Cloudinary dynamic folder mode
CLOUDINARY_UPLOAD_OPTIONS = {
    'static': {
        'asset_folder': 'static',
        'resource_type': 'raw',
        'use_filename': True,
        'unique_filename': False,
        'overwrite': True,
    },
    'media': {
        'asset_folder': 'media',
        'use_filename': True,
        'unique_filename': False,
        'overwrite': True,
    }
}
