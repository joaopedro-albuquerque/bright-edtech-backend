import os
import logging
import PyPDF2
from fastapi import UploadFile
from uuid import UUID, uuid4
from app.schemas.user_schema import PastaBase
from app.repositories.DocumentRepository import DocumentRepository
from app.services.GenerativeIAService import GenerativeIAService    
from app.services.S3Service import S3Service

logger = logging.getLogger(__name__)

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
        logger.info("DocumentGeneratorService inicializado com sucesso.")

    def criar_pasta_service(self, pasta: PastaBase) -> dict:
        logger.info(f"Iniciando criação de pasta. Dados: {pasta}")
        try:
            resultado = self.document_repo.criar_pasta(pasta)
            logger.info(f"Pasta criada com sucesso. ID: {resultado.get('id')}")
            return resultado
        except Exception as e:
            logger.error(f"Erro capturado ao criar pasta: {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível criar a pasta no momento.")

    def salvar_documento(self, documento, pasta_id: UUID, usuario_id: UUID, nome_documento: str) -> dict:
        logger.info(f"Iniciando salvamento do documento '{nome_documento}' (Usuário: {usuario_id}, Pasta: {pasta_id}).")
        file_ext = os.path.splitext(documento.filename)[1]
        logger.debug(f"Extensão do arquivo identificada: {file_ext}")

        try:
            logger.info("Criando registro inicial do documento no banco...")
            documento_salvo = self.document_repo.criar_documento(
                usuario_id=usuario_id,
                pasta_id=pasta_id,
                nome=nome_documento,
                file_ext=file_ext,
                nivel_conhecimento="iniciante"
            )

            documento_id = str(documento_salvo["id"])
            chave_s3 = self.s3_service.build_document_key(usuario_id, documento_id, file_ext)
            
            logger.info(f"Fazendo upload para o S3. Chave: {chave_s3}")
            self.s3_service.upload_file(documento.file, chave_s3)

            logger.info("Atualizando chave S3 no banco de dados...")
            documento_atualizado = self.document_repo.atualizar_chave_s3(documento_id, chave_s3)

            logger.info(f"Documento {documento_id} salvo e vinculado com sucesso.")
            return {
                "id": documento_atualizado["id"],
                "nome_documento": nome_documento,
                "s3_url": f"s3://{self.s3_service.bucket_name}/{chave_s3}",
                "status": documento_atualizado.get("status"),
                "resumo": documento_atualizado.get("resumo"),
                "chave_s3": documento_atualizado.get("chave_s3"),
                "documento": documento_atualizado,
            }
        except Exception as e:
            logger.error(f"Falha na esteira de salvamento do documento '{nome_documento}': {str(e)}", exc_info=True)
            raise RuntimeError("Ocorreu um erro ao salvar o documento ou enviá-lo para a nuvem.")

    def processar_novo_documento(self, usuario_id: str, pasta_id: str,  arquivo:  UUID):
        logger.info(f"Iniciando processamento de IA para o arquivo '{arquivo}' - (Usuário: {usuario_id}).")
        
        try:
             #TRECHO COMENTADO PARA MVP, ONDE BUSCO O DOCUMENTO PELA CHAVE
            #doc_uuid = str(uuid4())
            #chave_s3 = f"usuarios/{usuario_id}/documentos/{doc_uuid}.pdf"
            #self.s3_service.upload_file(file.file, chave_s3)

            documento = self.document_repo.buscar_chave_s3_por_documento_id_e_usuario(
                arquivo,
                usuario_id,
            )

            if not documento or not documento.get("chave_s3"):
                logger.warning(f"Documento não encontrado ou sem permissão. Doc ID: {arquivo}")
                raise ValueError("Documento não encontrado ou não pertence ao usuário.")
            
            chave_s3_str = documento["chave_s3"]

            fileS3 = self.s3_service.download_file(chave_s3_str)
            
            texto_do_pdf = self._extrair_texto_do_pdf(fileS3)
            logger.info(f"Texto extraído. Tamanho: {len(texto_do_pdf)} caracteres.")
            
            logger.info("Solicitando resumo à IA Generativa...")
            resumo_gerado = self.ia_service.gerar_resumo(texto_do_pdf)
            
            if not resumo_gerado:
                logger.warning("A IA retornou um resumo vazio.")
            else:
                logger.info("Resumo gerado com sucesso.")
            
            logger.info("Salvando documento processado no banco de dados...")
            
            resumo_salvo = self.document_repo.inserir_resumo_registro_documento(
                usuario_id=usuario_id,
                id_documento=arquivo,
                resumo=resumo_gerado
            )
                        
            logger.info("Processamento finalizado com sucesso.")
            return resumo_salvo
            
        except Exception as e:
            logger.error(f"Falha no processamento com IA do documento '{arquivo}': {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível processar e resumir o documento.")
    
    def buscar_resumo_documento(self, arquivo: UUID, usuario_id: UUID) -> dict:
            logger.info(f"Buscando resumo do documento '{arquivo}' (Usuário: {usuario_id}).")
            
            try:
                resultado = self.document_repo.buscar_resumo_por_id(arquivo, usuario_id)
                
                if not resultado or resultado.get("resumo") is None:
                    raise ValueError("Resumo não encontrado ou ainda não foi gerado.")
                    
                return resultado
                
            except ValueError as ve:
                raise ve
            except Exception as e:
                logger.error(f"Erro ao buscar resumo do documento '{arquivo}': {str(e)}", exc_info=True)
                raise RuntimeError("Não foi possível buscar o resumo no momento.")
            

    def gerar_pre_signed_url_visualizacao(self, documento_id: UUID, usuario_id: UUID) -> str:
        logger.info(f"Solicitando Pre-Signed URL. Doc: {documento_id} | User: {usuario_id}")
        try:
            documento = self.document_repo.buscar_chave_s3_por_documento_id_e_usuario(
                documento_id,
                usuario_id,
            )

            if not documento or not documento.get("chave_s3"):
                logger.warning(f"Documento não encontrado ou sem permissão. Doc ID: {documento_id}")
                raise ValueError("Documento não encontrado ou não pertence ao usuário.")

            logger.info("Gerando URL assinada no S3...")
            return self.s3_service.generate_presigned_url(documento["chave_s3"])
        except ValueError as ve:
            raise ve
        except Exception as e:
            logger.error(f"Erro ao gerar Pre-Signed URL para Doc {documento_id}: {str(e)}", exc_info=True)
            raise RuntimeError("Falha ao gerar link de visualização do documento.")

    def listar_pastas_raiz_por_usuario(self, usuario_id: UUID, limit: int, offset: int) -> list:
        logger.info(f"Listando pastas raiz para usuário {usuario_id}.")
        try:
            return self.document_repo.listar_pastas_raiz_por_usuario(usuario_id, limit, offset)
        except Exception as e:
            logger.error(f"Erro ao listar pastas raiz do usuário {usuario_id}: {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível carregar as pastas.")

    def listar_todas_pastas_por_usuario(self, usuario_id: UUID) -> list:
        logger.info(f"Listando todas as pastas para o usuário {usuario_id}.")
        try:
            return self.document_repo.listar_todas_pastas_por_usuario(usuario_id)
        except Exception as e:
            logger.error(f"Erro ao listar todas as pastas do usuário {usuario_id}: {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível carregar a estrutura de pastas.")
    
    def listar_conteudo_pasta(self, pasta_id: UUID, limit: int, offset: int) -> dict:
        logger.info(f"Listando conteúdo da pasta {pasta_id}.")
        try:
            return self.document_repo.listar_conteudo_pasta(pasta_id, limit, offset)
        except Exception as e:
            logger.error(f"Erro ao listar conteúdo da pasta {pasta_id}: {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível carregar o conteúdo da pasta.")

    def atualizar_pasta_nome(self, pasta_id: UUID, nome: str) -> dict | None:
        logger.info(f"Atualizando nome da pasta {pasta_id} para '{nome}'.")
        try:
            resultado = self.document_repo.atualizar_pasta_nome(pasta_id, nome)
            if not resultado:
                logger.warning(f"Pasta {pasta_id} não encontrada para atualização.")
            else:
                logger.info(f"Pasta {pasta_id} renomeada com sucesso.")
            return resultado
        except Exception as e:
            logger.error(f"Erro ao renomear pasta {pasta_id}: {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível renomear a pasta.")

    def deletar_pasta(self, pasta_id: UUID) -> bool:
        logger.warning(f"Solicitação de exclusão para a pasta {pasta_id}.")
        try:
            resultado = self.document_repo.deletar_pasta(pasta_id)
            if resultado:
                logger.info(f"Pasta {pasta_id} deletada com sucesso.")
            else:
                logger.warning(f"Pasta {pasta_id} não encontrada ou já deletada.")
            return resultado
        except Exception as e:
            logger.error(f"Erro ao deletar pasta {pasta_id}: {str(e)}", exc_info=True)
            raise RuntimeError("Não foi possível excluir a pasta. Verifique se ela está vazia.")

    # Helpers
    def _extrair_texto_do_pdf(self, file_stream) -> str:     
        try:
            file_stream.seek(0)
            
            leitor_pdf = PyPDF2.PdfReader(file_stream)
            total_paginas = len(leitor_pdf.pages)
            logger.debug(f"PDF carregado com {total_paginas} páginas.")
            
            texto_extraido = ""
            for i, pagina in enumerate(leitor_pdf.pages):
                texto_extraido += pagina.extract_text() + "\n"
                
            return texto_extraido.strip()
            
        except Exception as e:
            logger.error(f"Falha ao ler o binário do PDF: {str(e)}", exc_info=True)
            raise ValueError("O arquivo PDF está corrompido ou é ilegível.")
            
        finally:
            logger.debug("Retornando ponteiro do arquivo para o início.")
            file_stream.seek(0)