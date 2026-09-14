"""
Image Optimization Service
Handles image compression, resizing, format conversion, and CDN integration
"""

import os
from io import BytesIO
from PIL import Image, ImageOps
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class ImageOptimizer:
    """Optimize images for web performance"""
    
    # Quality settings
    DEFAULT_QUALITY = getattr(settings, 'THUMBNAIL_QUALITY', 85)
    WEBP_QUALITY = 80
    
    # Size presets
    SIZES = {
        'thumbnail': (150, 150),
        'small': (300, 300),
        'medium': (600, 600),
        'large': (1200, 1200),
        'hero': (1920, 1080),
    }
    
    @staticmethod
    def optimize_image(image_file, quality=None, max_size=None, convert_to_webp=True):
        """
        Optimize an uploaded image
        
        Args:
            image_file: Uploaded file object
            quality: JPEG quality (1-100)
            max_size: Maximum dimensions (width, height)
            convert_to_webp: Whether to convert to WebP format
            
        Returns:
            Optimized InMemoryUploadedFile
        """
        try:
            quality = quality or ImageOptimizer.DEFAULT_QUALITY
            
            # Open image
            img = Image.open(image_file)
            
            # Convert to RGB if necessary (for JPEG/WebP)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Resize if max_size specified
            if max_size:
                img = ImageOps.fit(img, max_size, Image.LANCZOS)
            
            # Optimize
            output = BytesIO()
            
            if convert_to_webp:
                img.save(output, format='WEBP', quality=ImageOptimizer.WEBP_QUALITY, optimize=True)
                extension = 'webp'
                content_type = 'image/webp'
            else:
                img.save(output, format='JPEG', quality=quality, optimize=True)
                extension = 'jpg'
                content_type = 'image/jpeg'
            
            output.seek(0)
            
            # Create new file object
            optimized_file = InMemoryUploadedFile(
                output,
                None,
                f"{image_file.name.rsplit('.', 1)[0]}.{extension}",
                content_type,
                output.getbuffer().nbytes,
                None
            )
            
            logger.info(f"Image optimized: {image_file.name} -> {optimized_file.name}")
            return optimized_file
            
        except Exception as e:
            logger.error(f"Image optimization failed: {str(e)}")
            return image_file
    
    @staticmethod
    def create_thumbnails(image_file, sizes=None):
        """
        Create multiple thumbnail sizes for an image
        
        Args:
            image_file: Image file object
            sizes: Dictionary of size names and dimensions
            
        Returns:
            Dictionary of thumbnail files
        """
        sizes = sizes or ImageOptimizer.SIZES
        thumbnails = {}
        
        try:
            img = Image.open(image_file)
            
            for size_name, dimensions in sizes.items():
                thumbnail = ImageOps.fit(img, dimensions, Image.LANCZOS)
                output = BytesIO()
                thumbnail.save(output, format='WEBP', quality=ImageOptimizer.WEBP_QUALITY, optimize=True)
                output.seek(0)
                
                thumbnails[size_name] = InMemoryUploadedFile(
                    output,
                    None,
                    f"{image_file.name.rsplit('.', 1)[0]}_{size_name}.webp",
                    'image/webp',
                    output.getbuffer().nbytes,
                    None
                )
            
            logger.info(f"Created {len(thumbnails)} thumbnails for {image_file.name}")
            return thumbnails
            
        except Exception as e:
            logger.error(f"Thumbnail creation failed: {str(e)}")
            return {}
    
    @staticmethod
    def get_optimized_url(original_url, size='medium'):
        """
        Get optimized image URL for a specific size
        
        Args:
            original_url: Original image URL
            size: Size variant (thumbnail, small, medium, large, hero)
            
        Returns:
            Optimized image URL
        """
        if not original_url:
            return None
            
        # If CDN is configured, use CDN URL
        cdn_base = getattr(settings, 'CDN_BASE_URL', None)
        if cdn_base:
            base_url = cdn_base
        else:
            base_url = original_url.rsplit('/', 1)[0]
        
        filename = original_url.rsplit('/', 1)[1]
        name, ext = os.path.splitext(filename)
        
        return f"{base_url}/{name}_{size}.webp"
    
    @staticmethod
    def analyze_image(image_file):
        """
        Analyze image properties
        
        Args:
            image_file: Image file object
            
        Returns:
            Dictionary with image metadata
        """
        try:
            img = Image.open(image_file)
            
            return {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.width,
                'height': img.height,
                'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info,
            }
        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}")
            return {}


class ImageCDNService:
    """Service for managing CDN integration"""
    
    CDN_ENABLED = False
    CDN_PROVIDER = None  # 'cloudinary', 'aws_s3', 'imgix', etc.
    CDN_BASE_URL = None
    
    @classmethod
    def initialize(cls):
        """Initialize CDN service based on settings"""
        cls.CDN_ENABLED = getattr(settings, 'CDN_ENABLED', False)
        cls.CDN_PROVIDER = getattr(settings, 'CDN_PROVIDER', None)
        cls.CDN_BASE_URL = getattr(settings, 'CDN_BASE_URL', None)
        
        if cls.CDN_ENABLED and cls.CDN_PROVIDER:
            logger.info(f"CDN initialized: {cls.CDN_PROVIDER}")
    
    @classmethod
    def upload_to_cdn(cls, image_file, path=None):
        """
        Upload image to CDN
        
        Args:
            image_file: Image file object
            path: Destination path on CDN
            
        Returns:
            CDN URL or None if upload fails
        """
        if not cls.CDN_ENABLED:
            return None
        
        try:
            if cls.CDN_PROVIDER == 'cloudinary':
                return cls._upload_to_cloudinary(image_file, path)
            elif cls.CDN_PROVIDER == 'aws_s3':
                return cls._upload_to_s3(image_file, path)
            else:
                logger.warning(f"Unsupported CDN provider: {cls.CDN_PROVIDER}")
                return None
        except Exception as e:
            logger.error(f"CDN upload failed: {str(e)}")
            return None
    
    @classmethod
    def _upload_to_cloudinary(cls, image_file, path=None):
        """Upload to Cloudinary"""
        try:
            import cloudinary.uploader
            import cloudinary.api
            
            result = cloudinary.uploader.upload(
                image_file,
                folder=path or 'properties',
                transformation=[
                    {'quality': 'auto', 'fetch_format': 'auto'},
                    {'width': 1200, 'crop': 'limit'}
                ]
            )
            
            return result['secure_url']
        except ImportError:
            logger.error("Cloudinary not installed")
            return None
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {str(e)}")
            return None
    
    @classmethod
    def _upload_to_s3(cls, image_file, path=None):
        """Upload to AWS S3"""
        try:
            import boto3
            from django.conf import settings
            
            s3 = boto3.client(
                's3',
                aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY'),
                region_name=getattr(settings, 'AWS_S3_REGION', 'us-east-1')
            )
            
            bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME')
            key = f"{path or 'properties'}/{image_file.name}"
            
            s3.upload_fileobj(
                image_file,
                bucket,
                key,
                ExtraArgs={
                    'ContentType': 'image/webp',
                    'CacheControl': 'max-age=31536000'  # 1 year
                }
            )
            
            return f"https://{bucket}.s3.amazonaws.com/{key}"
        except ImportError:
            logger.error("boto3 not installed")
            return None
        except Exception as e:
            logger.error(f"S3 upload failed: {str(e)}")
            return None
    
    @classmethod
    def get_cdn_url(cls, image_path, transformations=None):
        """
        Get CDN URL with transformations
        
        Args:
            image_path: Image path or public ID
            transformations: Dictionary of transformation parameters
            
        Returns:
            CDN URL
        """
        if not cls.CDN_ENABLED or not cls.CDN_BASE_URL:
            return image_path
        
        try:
            if cls.CDN_PROVIDER == 'cloudinary':
                return cls._get_cloudinary_url(image_path, transformations)
            elif cls.CDN_PROVIDER == 'imgix':
                return cls._get_imgix_url(image_path, transformations)
            else:
                return f"{cls.CDN_BASE_URL}/{image_path}"
        except Exception as e:
            logger.error(f"CDN URL generation failed: {str(e)}")
            return image_path
    
    @classmethod
    def _get_cloudinary_url(cls, image_path, transformations=None):
        """Get Cloudinary URL with transformations"""
        try:
            import cloudinary
            
            options = {
                'secure': True,
                'fetch_format': 'auto',
                'quality': 'auto',
            }
            
            if transformations:
                options.update(transformations)
            
            return cloudinary.CloudinaryImage(image_path).build_url(**options)
        except ImportError:
            logger.error("Cloudinary not installed")
            return image_path
        except Exception as e:
            logger.error(f"Cloudinary URL generation failed: {str(e)}")
            return image_path
    
    @classmethod
    def _get_imgix_url(cls, image_path, transformations=None):
        """Get Imgix URL with transformations"""
        try:
            from imgix_python import ImgixClient
            
            client = ImgixClient(
                domain=cls.CDN_BASE_URL.replace('https://', ''),
                use_https=True
            )
            
            params = {
                'auto': 'format,compress',
                'q': 80,
            }
            
            if transformations:
                params.update(transformations)
            
            return client.to_url(image_path, params)
        except ImportError:
            logger.error("imgix-python not installed")
            return image_path
        except Exception as e:
            logger.error(f"Imgix URL generation failed: {str(e)}")
            return image_path


# Initialize CDN service on module load
ImageCDNService.initialize()