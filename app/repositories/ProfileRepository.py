from uuid import UUID
from app.schemas.user_schema import Usuario, UsuarioBase

class ProfileRepository:
    def __init__(self, conn):
        self.conn = conn

    def criar_usuario(self, usuario: UsuarioBase) -> Usuario:
        with self.conn.cursor() as cursor:
            query = """
                INSERT INTO usuarios 
                (email, nome, estilo_preferido, formato_preferido, objetivos_estudo)
                VALUES (%s, %s, %s, %s, %s);
            """
            
            cursor.execute(query, (
                usuario.email,
                usuario.nome,
                usuario.estilo_preferido,
                usuario.formato_preferido,
                usuario.objetivos_estudo
            ))
            
            self.conn.commit()
            
            cursor.execute(
                "SELECT * FROM usuarios WHERE email = %s;",
                (usuario.email,)
            )
            row = cursor.fetchone()
            
            return Usuario(**row)
        
    def atualizar_usuario_por_id(self, user_id: UUID, usuario: UsuarioBase) -> Usuario | None:
        with self.conn.cursor() as cursor:
            query = """
                UPDATE usuarios
                SET email = %s,
                    nome = %s,
                    estilo_preferido = %s,
                    formato_preferido = %s,
                    objetivos_estudo = %s,
                    atualizado_em = now()
                WHERE id = %s;
            """

            cursor.execute(query, (
                usuario.email,
                usuario.nome,
                usuario.estilo_preferido,
                usuario.formato_preferido,
                usuario.objetivos_estudo,
                user_id
            ))

            self.conn.commit()
            
            cursor.execute(
                "SELECT * FROM usuarios WHERE id = %s;",
                (user_id,)
            )
            row = cursor.fetchone()

            return Usuario(**row) if row else None

    def buscar_usuario_por_id(self, user_id: UUID) -> Usuario | None:
        with self.conn.cursor() as cursor:
            query = """
                SELECT *
                FROM usuarios
                WHERE id = %s;
            """

            cursor.execute(query, (user_id,))
            row = cursor.fetchone()

            return Usuario(**row) if row else None

    def deletar_usuario_por_id(self, user_id: UUID) -> bool:
        with self.conn.cursor() as cursor:
            query = """
                DELETE FROM usuarios
                WHERE id = %s;
            """

            cursor.execute(query, (user_id,))
            deleted = cursor.rowcount > 0
            self.conn.commit()

            return deleted
