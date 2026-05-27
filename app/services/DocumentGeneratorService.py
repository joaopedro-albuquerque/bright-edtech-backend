import os
from uuid import UUID
from app.schemas.user_schema import PastaBase
from app.repositories.DocumentRepository import DocumentRepository
from app.services.S3Service import S3Service

class DocumentGeneratorService:
    def __init__(self, document_repo: DocumentRepository):
        self.document_repo = document_repo
        self.s3_service = S3Service()

    def criar_pasta_service(self, pasta: PastaBase) -> dict:
        return self.document_repo.criar_pasta(pasta)
    
    def salvar_documento(self, documento, pasta_id: UUID, usuario_id: UUID, nome_documento: str) -> dict:
        file_ext = os.path.splitext(documento.filename)[1]

        documento_salvo = self.document_repo.criar_documento(
            usuario_id=usuario_id,
            pasta_id=pasta_id,
            nome=nome_documento,
            file_ext=file_ext,
            nivel_conhecimento="iniciante"
        )

        if not documento_salvo or "id" not in documento_salvo:
            raise RuntimeError("Falha ao inserir documento no banco")

        documento_id = str(documento_salvo["id"])
        chave_s3 = self.s3_service.build_document_key(usuario_id, documento_id, file_ext)

        self.s3_service.upload_file(documento.file, chave_s3)

        documento_atualizado = self.document_repo.atualizar_chave_s3(documento_id, chave_s3)

        return {
            "message": "Documento salvo com sucesso",
            "documento": documento_atualizado,
            "s3_url": f"s3://{self.s3_service.bucket_name}/{chave_s3}"
        }
    
    #alterar modelagem para permitir s3key null no primeiro momento