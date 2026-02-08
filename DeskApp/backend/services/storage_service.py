# backend/services/storage_service.py
import os
import uuid
from datetime import timedelta
from google.cloud import storage

class StorageService:
    def __init__(self, bucket_name: str = None):
        self.bucket_name = bucket_name or os.getenv('GCS_BUCKET')
        if not self.bucket_name:
            raise RuntimeError('GCS_BUCKET environment variable not set')
        self.client = storage.Client()
        self.bucket = self.client.bucket(self.bucket_name)

    def upload_file(self, local_path: str, destination_path: str) -> dict:
        """
        Uploads a file to GCS and returns metadata including public URL.
        """
        blob = self.bucket.blob(destination_path)
        blob.upload_from_filename(local_path)
        
        try:
            url = blob.public_url
        except Exception:
            url = None

        return {
            'bucket': self.bucket_name,
            'path': destination_path,
            'public_url': url
        }

    def upload_file_bytes(self, file_bytes: bytes, destination_path: str) -> dict:
        blob = self.bucket.blob(destination_path)
        blob.upload_from_string(file_bytes)
        
        try:
            url = blob.public_url
        except Exception:
            url = None
            
        return {
            'bucket': self.bucket_name,
            'path': destination_path,
            'public_url': url
        }
    
    def generate_signed_url(self, blob_path: str, expiration: int = 3600) -> str:
        """
        Generate a signed URL for accessing a private GCS file
        
        Args:
            blob_path: Path to the blob in GCS (e.g., "users/123/captures/abc.png")
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Signed URL string
        """
        
        # Remove gs:// prefix if present
        if blob_path.startswith('gs://'):
            blob_path = blob_path.replace(f'gs://{self.bucket_name}/', '')
        
        blob = self.bucket.blob(blob_path)
        
        # Generate signed URL
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiration),
            method="GET"
        )
        
        return url
    
    def delete_file(self, blob_path: str) -> bool:
        """Delete a file from GCS"""
        try:
            blob = self.bucket.blob(blob_path)
            blob.delete()
            return True
        except Exception as e:
            print(f"[STORAGE] Failed to delete {blob_path}: {e}")
            return False
    
    def file_exists(self, blob_path: str) -> bool:
        """Check if a file exists in GCS"""
        blob = self.bucket.blob(blob_path)
        return blob.exists()