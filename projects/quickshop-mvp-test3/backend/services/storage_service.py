import boto3
from botocore.exceptions import ClientError
from typing import Dict, Optional, List
from core.config import settings
import uuid
import os

class S3StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID.get_secret_value(),
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY.get_secret_value()
        )
        self.bucket_name = settings.AWS_S3_BUCKET_NAME

    def upload_product_image(self, file, product_id: str) -> Dict[str, str]:
        """
        Upload product image to S3 with unique filename
        
        Args:
            file: File object to upload
            product_id: ID of the product associated with the image
        
        Returns:
            Dict with upload details
        """
        try:
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"products/{product_id}/{uuid.uuid4()}{file_extension}"
            
            # Upload to S3
            self.s3_client.upload_fileobj(
                file.file, 
                self.bucket_name, 
                unique_filename,
                ExtraArgs={
                    'ContentType': file.content_type,
                    'ACL': 'public-read'  # Adjust based on your security requirements
                }
            )
            
            # Construct public URL
            public_url = f"https://{self.bucket_name}.s3.amazonaws.com/{unique_filename}"
            
            return {
                'status': 'success',
                'filename': unique_filename,
                'public_url': public_url
            }
        
        except ClientError as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def delete_product_image(self, image_path: str) -> Dict[str, str]:
        """
        Delete a product image from S3
        
        Args:
            image_path: Full or partial S3 path of the image to delete
        
        Returns:
            Dict with deletion status
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=image_path
            )
            
            return {
                'status': 'success',
                'message': 'Image deleted successfully'
            }
        
        except ClientError as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def list_product_images(self, product_id: str) -> List[Dict[str, str]]:
        """
        List all images for a specific product
        
        Args:
            product_id: ID of the product to list images for
        
        Returns:
            List of image details
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"products/{product_id}/"
            )
            
            images = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    images.append({
                        'key': obj['Key'],
                        'public_url': f"https://{self.bucket_name}.s3.amazonaws.com/{obj['Key']}",
                        'last_modified': obj['LastModified']
                    })
            
            return images
        
        except ClientError as e:
            return []

storage_service = S3StorageService()