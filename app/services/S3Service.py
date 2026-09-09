import json
import os
import io
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

    def generate_presigned_url(self, key: str, expiration: int = 300) -> str:
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expiration
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"Falha ao gerar URL pré-assinada para S3: {exc}") from exc
        
    def download_file(self, key: str) -> io.BytesIO:
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            return io.BytesIO(response['Body'].read())
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"Falha ao baixar arquivo do S3: {exc}") from exc

    def upload_text(self, content: str, key: str, content_type: str = "text/markdown") -> dict:
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content.encode("utf-8"),
                ContentType=content_type,
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"Falha ao enviar texto para S3: {exc}") from exc

        return {"bucket": self.bucket_name, "key": key, "s3_url": f"s3://{self.bucket_name}/{key}"}

    def upload_json(self, data, key: str) -> dict:
        return self.upload_text(json.dumps(data, ensure_ascii=False, indent=2), key, content_type="application/json")

    def download_json(self, key: str):
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            return json.loads(response["Body"].read())
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(f"Falha ao baixar JSON do S3: {exc}") from exc
