import os
import uuid
import mimetypes
from typing import BinaryIO

from app.interfaces.storage import StorageBackend


class S3StorageBackend(StorageBackend):
    def __init__(self, bucket_name: str, region: str = "us-east-1", prefix: str = ""):
        self.bucket_name = bucket_name
        self.region = region
        self.prefix = prefix.strip("/")

        try:
            import boto3
            import botocore
        except ImportError:
            raise ImportError("boto3 is required for S3 storage. Install with: pip install boto3")

        self.client = boto3.client("s3", region_name=region)
        self._ensure_bucket()

    def _ensure_bucket(self):
        import botocore
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except botocore.exceptions.ClientError:
            self.client.create_bucket(
                Bucket=self.bucket_name,
                CreateBucketConfiguration={"LocationConstraint": self.region},
            )

    def save(self, filename: str, content: BinaryIO) -> str:
        safe_name = self._clean_filename(filename)
        unique_id = uuid.uuid4().hex
        key = f"{self.prefix}/{unique_id[:2]}/{unique_id[2:4]}/{unique_id}_{safe_name}" if self.prefix else f"{unique_id[:2]}/{unique_id[2:4]}/{unique_id}_{safe_name}"
        key = key.lstrip("/")

        content_type, _ = mimetypes.guess_type(filename)
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        content.seek(0)
        self.client.upload_fileobj(content, self.bucket_name, key, ExtraArgs=extra_args or None)
        return key

    def get_path(self, storage_path: str) -> str:
        import tempfile
        ext = os.path.splitext(storage_path)[1]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        self.client.download_fileobj(self.bucket_name, storage_path, tmp)
        tmp.close()
        return tmp.name

    def _clean_filename(self, filename: str) -> str:
        from werkzeug.utils import secure_filename
        return secure_filename(filename) or uuid.uuid4().hex
