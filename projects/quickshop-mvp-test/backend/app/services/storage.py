import os
import boto3
from botocore.exceptions import ClientError
from typing import Optional, List
from fastapi import UploadFile

class S3StorageService:
    def __init__(self):
        # Use environment variables for AWS credentials
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        if not self.bucket_name:
            raise ValueError("S3 Bucket name not configured")

    def upload_product_image(
        self, 
        file: UploadFile, 
        product_id: str, 
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload a product image to S3
        
        :param file: Image file to upload
        :param product_id: ID of the product
        :param content_type: Optional MIME type
        :return: Public URL of uploaded image
        """
        try:
            # Generate a unique filename
            filename = f"products/{product_id}/{file.filename}"
            
            # Upload file
            self.s3_client.upload_fileobj(
                file.file, 
                self.bucket_name, 
                filename,
                ExtraArgs={
                    'ContentType': content_type or file.content_type,
                    'ACL': 'public-read'
                }
            )
            
            # Construct public URL
            return f"https://{self.bucket_name}.s3.amazonaws.com/{filename}"
        except ClientError as e:
            # Log error in actual implementation
            print(f"S3 upload failed: {str(e)}")
            raise

    def delete_product_images(self, image_urls: List[str]) -> bool:
        """
        Delete product images from S3
        
        :param image_urls: List of image URLs to delete
        :return: True if successful, False otherwise
        """
        try:
            # Convert URLs to S3 object keys
            objects = [
                {'Key': url.split(f"{self.bucket_name}.s3.amazonaws.com/")[1]} 
                for url in image_urls 
                if self.bucket_name in url
            ]
            
            if not objects:
                return True
            
            # Bulk delete
            response = self.s3_client.delete_objects(
                Bucket=self.bucket_name,
                Delete={'Objects': objects}
            )
            
            return len(response.get('Deleted', [])) == len(objects)
        except ClientError as e:
            # Log error in actual implementation
            print(f"S3 delete failed: {str(e)}")
            return False

s3_storage_service = S3StorageService()