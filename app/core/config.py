import os

# Versão atual do Termo de Uso / Consentimento LGPD exibido no cadastro.
# Ao editar o texto do termo no front (rota /termos), incrementar este valor
# para forçar novos aceites de quem ainda não cadastrou — usuários já
# cadastrados não são afetados (não há gate retroativo, por decisão de
# produto registrada na feature de consentimento LGPD).
TERMOS_DE_USO_VERSAO = "1.0"


class Settings:
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    s3_bucket_name: str | None = os.getenv("S3_BUCKET_NAME")

    bedrock_region: str = os.getenv("BEDROCK_REGION", os.getenv("AWS_REGION", "us-east-1"))
    bedrock_model_summary: str = os.getenv(
        "BEDROCK_MODEL_SUMMARY", "anthropic.claude-3-5-sonnet-20241022-v2:0"
    )
    bedrock_model_extract: str = os.getenv(
        "BEDROCK_MODEL_EXTRACT", "anthropic.claude-3-5-haiku-20241022-v1:0"
    )


settings = Settings()
