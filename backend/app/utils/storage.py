import os
from abc import ABC, abstractmethod
from backend.app.core.config import settings

class StorageInterface(ABC):
    @abstractmethod
    def save_file(self, content: bytes, filename: str) -> str:
        """Save file contents and return file URL / path"""
        pass

    @abstractmethod
    def delete_file(self, file_url: str) -> bool:
        """Delete file by its URL or path"""
        pass


class LocalStorage(StorageInterface):
    def __init__(self, upload_dir: str = None):
        self.upload_dir = upload_dir or settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)

    def save_file(self, content: bytes, filename: str) -> str:
        # Avoid duplicate names by prefixing a timestamp or index if needed
        # For simplicity, write directly to files directory
        file_path = os.path.join(self.upload_dir, filename)
        with open(file_path, "wb") as f:
            f.write(content)
        # Return path relative to the workspace, or just the filename for backend route serving
        return f"/api/v1/publications/files/{filename}"

    def delete_file(self, file_url: str) -> bool:
        filename = file_url.split("/")[-1]
        file_path = os.path.join(self.upload_dir, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False


class S3Storage(StorageInterface):
    def __init__(self):
        self.bucket = settings.AWS_S3_BUCKET
        self.access_key = settings.AWS_ACCESS_KEY_ID
        self.secret_key = settings.AWS_SECRET_ACCESS_KEY
        # In a real environment, we'd import boto3
        # Here we will check if credentials are set, and mock if not
        self.use_mock = not (self.access_key and self.secret_key and self.bucket)

    def save_file(self, content: bytes, filename: str) -> str:
        if self.use_mock:
            # Fall back to local filesystem storage if S3 credentials not provided
            local = LocalStorage()
            return local.save_file(content, filename)
        try:
            import boto3
            s3 = boto3.client(
                "s3",
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            )
            s3.put_object(Bucket=self.bucket, Key=filename, Body=content)
            return f"https://{self.bucket}.s3.amazonaws.com/{filename}"
        except Exception as e:
            # Fallback to local on error
            local = LocalStorage()
            return local.save_file(content, filename)

    def delete_file(self, file_url: str) -> bool:
        if self.use_mock:
            local = LocalStorage()
            return local.delete_file(file_url)
        try:
            import boto3
            filename = file_url.split("/")[-1]
            s3 = boto3.client(
                "s3",
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            )
            s3.delete_object(Bucket=self.bucket, Key=filename)
            return True
        except Exception:
            return False


def get_storage() -> StorageInterface:
    if settings.STORAGE_PROVIDER == "s3":
        return S3Storage()
    return LocalStorage()
