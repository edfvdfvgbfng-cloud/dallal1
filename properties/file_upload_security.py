"""
File Upload Security Module
Provides secure file upload validation and processing
"""

import os
import mimetypes
import magic
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Allowed file types and their MIME types
ALLOWED_IMAGE_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/gif': ['.gif'],
    'image/webp': ['.webp'],
    'image/svg+xml': ['.svg'],
}

ALLOWED_DOCUMENT_TYPES = {
    'application/pdf': ['.pdf'],
    'application/msword': ['.doc'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/vnd.ms-excel': ['.xls'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
}

ALLOWED_VIDEO_TYPES = {
    'video/mp4': ['.mp4'],
    'video/webm': ['.webm'],
    'video/quicktime': ['.mov'],
}

ALLOWED_AUDIO_TYPES = {
    'audio/mpeg': ['.mp3'],
    'audio/wav': ['.wav'],
    'audio/ogg': ['.ogg'],
}

# Maximum file sizes (in bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_DOCUMENT_SIZE = 5 * 1024 * 1024  # 5MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
MAX_AUDIO_SIZE = 20 * 1024 * 1024  # 20MB

# Dangerous file extensions to block
DANGEROUS_EXTENSIONS = [
    '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
    '.sh', '.ps1', '.php', '.asp', '.aspx', '.jsp', '.py', '.rb', '.pl',
    '.dll', '.sys', '.drv', '.cpl', '.msi', '.msp', '.deb', '.rpm',
    '.app', '.dmg', '.pkg', '.sit', '.sitx', '.zipx', '.torrent',
]


def validate_file_type(file, allowed_types):
    """
    Validate file type using magic bytes (more secure than extension)
    """
    try:
        # Read file content for magic byte detection
        file.seek(0)
        content = file.read(2048)
        file.seek(0)
        
        # Use python-magic for real MIME type detection
        mime = magic.from_buffer(content, mime=True)
        
        if mime not in allowed_types:
            raise ValidationError(
                _(f'نوع الملف غير مسموح. الأنواع المسموحة: {", ".join(allowed_types.keys())}')
            )
        
        return mime
    except Exception as e:
        raise ValidationError(_(f'خطأ في التحقق من نوع الملف: {str(e)}'))


def validate_file_extension(filename, allowed_extensions):
    """
    Validate file extension
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            _(f'امتداد الملف غير مسموح. الامتدادات المسموحة: {", ".join(allowed_extensions)}')
        )
    return ext


def validate_file_size(file, max_size):
    """
    Validate file size
    """
    if file.size > max_size:
        size_mb = max_size / (1024 * 1024)
        raise ValidationError(
            _(f'حجم الملف يتجاوز الحد المسموح ({size_mb}MB)')
        )
    return True


def sanitize_filename(filename):
    """
    Sanitize filename to prevent path traversal and other attacks
    """
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    dangerous_chars = ['..', '/', '\\', '\0', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        filename = filename.replace(char, '')
    
    # Check for dangerous extensions
    ext = os.path.splitext(filename)[1].lower()
    if ext in DANGEROUS_EXTENSIONS:
        raise ValidationError(_(f'نوع الملف خطير وغير مسموح'))
    
    return filename


def validate_image_upload(file):
    """
    Complete validation for image uploads
    """
    # Validate extension
    allowed_extensions = []
    for ext_list in ALLOWED_IMAGE_TYPES.values():
        allowed_extensions.extend(ext_list)
    validate_file_extension(file.name, allowed_extensions)
    
    # Validate size
    validate_file_size(file, MAX_IMAGE_SIZE)
    
    # Validate MIME type
    mime = validate_file_type(file, ALLOWED_IMAGE_TYPES)
    
    # Sanitize filename
    safe_name = sanitize_filename(file.name)
    
    return {
        'mime_type': mime,
        'safe_name': safe_name,
        'max_size': MAX_IMAGE_SIZE
    }


def validate_document_upload(file):
    """
    Complete validation for document uploads
    """
    # Validate extension
    allowed_extensions = []
    for ext_list in ALLOWED_DOCUMENT_TYPES.values():
        allowed_extensions.extend(ext_list)
    validate_file_extension(file.name, allowed_extensions)
    
    # Validate size
    validate_file_size(file, MAX_DOCUMENT_SIZE)
    
    # Validate MIME type
    mime = validate_file_type(file, ALLOWED_DOCUMENT_TYPES)
    
    # Sanitize filename
    safe_name = sanitize_filename(file.name)
    
    return {
        'mime_type': mime,
        'safe_name': safe_name,
        'max_size': MAX_DOCUMENT_SIZE
    }


def validate_video_upload(file):
    """
    Complete validation for video uploads
    """
    # Validate extension
    allowed_extensions = []
    for ext_list in ALLOWED_VIDEO_TYPES.values():
        allowed_extensions.extend(ext_list)
    validate_file_extension(file.name, allowed_extensions)
    
    # Validate size
    validate_file_size(file, MAX_VIDEO_SIZE)
    
    # Validate MIME type
    mime = validate_file_type(file, ALLOWED_VIDEO_TYPES)
    
    # Sanitize filename
    safe_name = sanitize_filename(file.name)
    
    return {
        'mime_type': mime,
        'safe_name': safe_name,
        'max_size': MAX_VIDEO_SIZE
    }


def validate_audio_upload(file):
    """
    Complete validation for audio uploads
    """
    # Validate extension
    allowed_extensions = []
    for ext_list in ALLOWED_AUDIO_TYPES.values():
        allowed_extensions.extend(ext_list)
    validate_file_extension(file.name, allowed_extensions)
    
    # Validate size
    validate_file_size(file, MAX_AUDIO_SIZE)
    
    # Validate MIME type
    mime = validate_file_type(file, ALLOWED_AUDIO_TYPES)
    
    # Sanitize filename
    safe_name = sanitize_filename(file.name)
    
    return {
        'mime_type': mime,
        'safe_name': safe_name,
        'max_size': MAX_AUDIO_SIZE
    }


def validate_contract_document(file):
    """
    Special validation for contract documents (PDF only)
    """
    if not file.name.lower().endswith('.pdf'):
        raise ValidationError(_('يجب أن تكون وثائق العقود بصيغة PDF فقط'))
    
    validate_file_size(file, MAX_DOCUMENT_SIZE)
    
    # Validate MIME type
    mime = validate_file_type(file, {'application/pdf': ['.pdf']})
    
    safe_name = sanitize_filename(file.name)
    
    return {
        'mime_type': mime,
        'safe_name': safe_name,
        'max_size': MAX_DOCUMENT_SIZE
    }


def validate_property_image(file):
    """
    Special validation for property images
    """
    return validate_image_upload(file)


def validate_broker_profile_image(file):
    """
    Special validation for broker profile images
    """
    result = validate_image_upload(file)
    # Additional size limit for profile images (2MB)
    if file.size > 2 * 1024 * 1024:
        raise ValidationError(_('حجم صورة الملف الشخصي يجب أن يكون أقل من 2MB'))
    return result


def scan_for_malware(file):
    """
    Basic malware scan (placeholder - integrate with real antivirus in production)
    """
    # In production, integrate with ClamAV or similar
    # For now, just check for embedded scripts in images
    try:
        file.seek(0)
        content = file.read(8192)
        file.seek(0)
        
        # Check for script tags in files that shouldn't have them
        dangerous_patterns = [
            b'<script',
            b'javascript:',
            b'data:text/html',
            b'<?php',
            b'<%',
        ]
        
        for pattern in dangerous_patterns:
            if pattern in content:
                raise ValidationError(_('تم اكتشاف محتوى مشبوه في الملف'))
        
        return True
    except Exception as e:
        raise ValidationError(_(f'خطأ في فحص الملف: {str(e)}'))


def secure_file_upload(file, upload_type='image'):
    """
    Main function for secure file upload validation
    """
    if not file:
        raise ValidationError(_('لم يتم توفير ملف'))
    
    # Sanitize filename first
    safe_name = sanitize_filename(file.name)
    
    # Route to appropriate validator
    validators = {
        'image': validate_image_upload,
        'document': validate_document_upload,
        'video': validate_video_upload,
        'audio': validate_audio_upload,
        'contract': validate_contract_document,
        'property_image': validate_property_image,
        'broker_profile': validate_broker_profile_image,
    }
    
    validator = validators.get(upload_type, validate_image_upload)
    result = validator(file)
    
    # Scan for malware
    scan_for_malware(file)
    
    return result