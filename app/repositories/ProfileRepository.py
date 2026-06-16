from uuid import UUID
from app.schemas.user_schema import Usuario, UsuarioBase

class ProfileRepository:
    def __init__(self, conn):
        self.conn = conn

    def criar_usuario(self, usuario: UsuarioBase) -> Usuario:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    INSERT INTO usuarios 
                    (email, nome, estilo_preferido, formato_preferido, objetivos_estudo, cognito_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING *;
                """
                
                cursor.execute(query, (
                    usuario.email,
                    usuario.nome,
                    usuario.estilo_preferido,
                    usuario.formato_preferido,
                    usuario.objetivos_estudo,
                    usuario.cognito_id 
                ))
                
                row = cursor.fetchone()
                
                if not row:
                    raise RuntimeError("INSERT executado, mas RETURNING falhou ao devolver o usuário.")
                
                self.conn.commit()
                return Usuario(**row)
                
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Erro no banco de dados ao criar usuário: {e}")
        
    def atualizar_usuario_por_id(self, user_id: UUID, usuario: UsuarioBase) -> Usuario | None:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    UPDATE usuarios
                    SET email = %s,
                        nome = %s,
                        estilo_preferido = %s,
                        formato_preferido = %s,
                        objetivos_estudo = %s,
                        atualizado_em = now()
                    WHERE id = %s
                    RETURNING *;
                """

                cursor.execute(query, (
                    usuario.email,
                    usuario.nome,
                    usuario.estilo_preferido,
                    usuario.formato_preferido,
                    usuario.objetivos_estudo,
                    user_id
                ))

                row = cursor.fetchone()
                
                if not row:
                    self.conn.rollback()
                    return None
                    
                self.conn.commit()
                return Usuario(**row)
                
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Erro no banco de dados ao atualizar usuário: {e}")

    def buscar_usuario_por_id(self, user_id: UUID) -> Usuario | None:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    SELECT *
                    FROM usuarios
                    WHERE id = %s;
                """

                cursor.execute(query, (user_id,))
                row = cursor.fetchone()

                return Usuario(**row) if row else None
                
        except Exception as e:
            raise RuntimeError(f"Erro no banco de dados ao buscar usuário por ID: {e}")

    def deletar_usuario_por_id(self, user_id: UUID) -> bool:
        try:
            with self.conn.cursor() as cursor:
                query = """
                    DELETE FROM usuarios
                    WHERE id = %s;
                """

                cursor.execute(query, (user_id,))
                deleted = cursor.rowcount > 0
                self.conn.commit()

                return deleted
                
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Erro no banco de dados ao deletar usuário: {e}")

    def buscar_usuario_por_cognito_id(self, cognito_id: str) -> Usuario | None:
            try:
                with self.conn.cursor() as cursor:
                    query = """
                        SELECT *
                        FROM usuarios
                        WHERE cognito_id = %s;
                    """
                    cursor.execute(query, (cognito_id,))
                    row = cursor.fetchone()

                    return Usuario(**row) if row else None
                    
            except Exception as e:
                raise RuntimeError(f"Erro no banco de dados ao buscar usuário por Cognito ID: {e}")