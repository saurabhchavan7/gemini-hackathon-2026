import os
import uuid
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
        # Make public if desired; keep private by default. Here we'll return signed URL
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
