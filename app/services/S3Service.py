import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError


class S3Service:
    def __init__(self, bucket_name: str | None = None):
        self.bucket_name = bucket_name or os.getenv("S3_BUCKET_NAME")
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME is required")

        self.client = boto3.client(
            "s3",
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )

    def build_document_key(self, usuario_id: str, documento_id: str, file_ext: str) -> str:
        return f"usuarios/{usuario_id}/documentos/{documento_id}{file_ext}"

    def upload_file(self, file_obj, key: str) -> dict:
        try:
            self.client.upload_fileobj(file_obj, self.bucket_name, key)
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"Falha no upload para S3: {exc}") from exc

        return {
            "bucket": self.bucket_name,
            "key": key,
            "s3_url": f"s3://{self.bucket_name}/{key}"
        }
