import os
import PyPDF2
from fastapi import UploadFile
from uuid import UUID, uuid4
from app.schemas.user_schema import PastaBase
from app.repositories.DocumentRepository import DocumentRepository
from app.services.GenerativeIAService import GenerativeIAService    
from app.services.S3Service import S3Service

class DocumentGeneratorService:
    def __init__(
        self,
        document_repo: DocumentRepository,
        s3_service: S3Service | None = None,
        ia_service: GenerativeIAService | None = None,
    ):
        self.document_repo = document_repo
        self.s3_service = s3_service or S3Service()
        self.ia_service = ia_service or GenerativeIAService()

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

    def processar_novo_documento(self, usuario_id: str, pasta_id: str, nome: str, file: UploadFile):
        doc_uuid = str(uuid4())
        chave_s3 = f"usuarios/{usuario_id}/documentos/{doc_uuid}.pdf"
        
        self.s3_service.upload_file(file.file, chave_s3)
        
        texto_do_pdf = self._extrair_texto_do_pdf(file.file)
        resumo_gerado = self.ia_service.gerar_resumo(texto_do_pdf)
        
        documento_salvo = self.document_repo.inserir_documento(
            usuario_id=usuario_id,
            pasta_id=pasta_id,
            nome=nome,
            chave_s3=chave_s3,
            resumo=resumo_gerado
        )
        
        return documento_salvo

    # Pastas (wrappers para o repository)
    def listar_pastas_raiz_por_usuario(self, usuario_id: UUID, limit: int, offset: int) -> list:
        return self.document_repo.listar_pastas_raiz_por_usuario(usuario_id, limit, offset)

    def listar_todas_pastas_por_usuario(self, usuario_id: UUID) -> list:
        return self.document_repo.listar_todas_pastas_por_usuario(usuario_id)
    
    def listar_conteudo_pasta(self, pasta_id: UUID, limit: int, offset: int) -> dict:
        return self.document_repo.listar_conteudo_pasta(pasta_id, limit, offset)

    def atualizar_pasta_nome(self, pasta_id: UUID, nome: str) -> dict | None:
        return self.document_repo.atualizar_pasta_nome(pasta_id, nome)

    def deletar_pasta(self, pasta_id: UUID) -> bool:
        return self.document_repo.deletar_pasta(pasta_id)

    # Helpers
    def _extrair_texto_do_pdf(self, file_stream) -> str:     
        try:
            file_stream.seek(0)
            
            leitor_pdf = PyPDF2.PdfReader(file_stream)
            
            texto_extraido = ""
            for pagina in leitor_pdf.pages:
                texto_extraido += pagina.extract_text() + "\n"
                
            return texto_extraido.strip()
            
        except Exception as e:
            raise ValueError(f"Falha ao ler o conteúdo do PDF: {str(e)}")
            
        finally:
            file_stream.seek(0)