import os
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException
from typing import Optional

class S3StorageService:
    def __init__(self):
        # Use environment variables for secure configuration
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_S3_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('AWS_S3_BUCKET_NAME', 'quickshop-product-images')

    def upload_product_image(
        self, 
        file: UploadFile, 
        product_id: str, 
        file_extension: Optional[str] = None
    ) -> str:
        """
        Upload a product image to S3
        
        :param file: File to upload
        :param product_id: Unique identifier for the product
        :param file_extension: Optional file extension override
        :return: Public URL of the uploaded image
        """
        # Determine file extension
        if not file_extension:
            file_extension = file.filename.split('.')[-1]
        
        # Generate a unique filename
        s3_filename = f"products/{product_id}.{file_extension}"
        
        try:
            # Upload file to S3
            self.s3_client.upload_fileobj(
                file.file, 
                self.bucket_name, 
                s3_filename,
                ExtraArgs={
                    'ContentType': f'image/{file_extension}',
                    'ACL': 'public-read'  # Make image publicly accessible
                }
            )
            
            # Construct public URL
            public_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_filename}"
            return public_url
        
        except ClientError as e:
            # Handle S3 specific errors
            raise HTTPException(
                status_code=500, 
                detail=f"S3 Upload Error: {str(e)}"
            )

    def delete_product_image(self, product_id: str, file_extension: str) -> bool:
        """
        Delete a product image from S3
        
        :param product_id: Unique identifier for the product
        :param file_extension: File extension of the image
        :return: True if deletion successful
        """
        s3_filename = f"products/{product_id}.{file_extension}"
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name, 
                Key=s3_filename
            )
            return True
        except ClientError as e:
            # Log error securely
            raise HTTPException(
                status_code=500, 
                detail=f"S3 Deletion Error: {str(e)}"
            )

# Create a singleton storage service
storage_service = S3StorageService()