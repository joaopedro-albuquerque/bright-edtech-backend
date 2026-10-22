class AppException(Exception):
    code: int = 9000
    http_status: int = 500
    message: str = "Ocorreu um erro inesperado."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message
        super().__init__(self.message)


class InfrastructureError(AppException):
    code = 9000
    http_status = 500
    message = "Erro interno de infraestrutura."


class DatabaseError(InfrastructureError):
    code = 9001
    message = "Erro ao acessar o banco de dados."


class StorageError(InfrastructureError):
    code = 9002
    http_status = 502
    message = "Erro ao acessar o armazenamento de arquivos."


class AiGenerationError(InfrastructureError):
    code = 9003
    http_status = 502
    message = "Erro ao gerar conteúdo com IA."


class ModeracaoIndisponivelError(InfrastructureError):
    code = 9004
    http_status = 503
    message = "Estamos com problemas internos no momento. Tente novamente em alguns instantes."


class UnexpectedError(AppException):
    code = 9999
    http_status = 500
    message = "Erro interno inesperado."


class DocumentError(AppException):
    code = 1000
    http_status = 500
    message = "Erro ao processar documento."


class DocumentNotFoundError(DocumentError):
    code = 1001
    http_status = 404
    message = "Documento ou pasta não encontrado."


class ConteudoImproprioError(DocumentError):
    code = 1005
    http_status = 422
    message = "Este documento contém conteúdo que não é permitido na plataforma."


class DocumentDatabaseError(DocumentError):
    code = 1002
    http_status = 500
    message = "Erro no banco de dados ao processar documento/pasta."


class ProfileError(AppException):
    code = 2000
    http_status = 500
    message = "Erro ao processar perfil do usuário."


class ProfileNotFoundError(ProfileError):
    code = 2001
    http_status = 404
    message = "Usuário não encontrado."


class ProfileDatabaseError(ProfileError):
    code = 2002
    http_status = 500
    message = "Erro no banco de dados ao processar usuário."


class FlashcardError(AppException):
    code = 3000
    http_status = 500
    message = "Erro ao processar flashcard."


class FlashcardNotFoundError(FlashcardError):
    code = 3001
    http_status = 404
    message = "Flashcard não encontrado."


class FlashcardDatabaseError(FlashcardError):
    code = 3002
    http_status = 500
    message = "Erro no banco de dados ao processar flashcard."


class QuizError(AppException):
    code = 4000
    http_status = 500
    message = "Erro ao processar quiz."


class QuizNotFoundError(QuizError):
    code = 4001
    http_status = 404
    message = "Quiz não encontrado."


class QuizDatabaseError(QuizError):
    code = 4002
    http_status = 500
    message = "Erro no banco de dados ao processar quiz."


class ResumoError(AppException):
    code = 5000
    http_status = 500
    message = "Erro ao processar resumo."


class ResumoNotFoundError(ResumoError):
    code = 5001
    http_status = 404
    message = "Resumo não encontrado."


class ResumoDatabaseError(ResumoError):
    code = 5002
    http_status = 500
    message = "Erro no banco de dados ao processar resumo."


class RevisaoError(AppException):
    code = 6000
    http_status = 500
    message = "Erro ao processar revisão."


class RevisaoNotFoundError(RevisaoError):
    code = 6001
    http_status = 404
    message = "Item de revisão não encontrado."


class RevisaoDatabaseError(RevisaoError):
    code = 6002
    http_status = 500
    message = "Erro no banco de dados ao processar revisão."


class DashboardError(AppException):
    code = 7000
    http_status = 500
    message = "Erro ao processar dashboard."


class DashboardDatabaseError(DashboardError):
    code = 7001
    http_status = 500
    message = "Erro no banco de dados ao processar dashboard."


from dataclasses import dataclass


@dataclass(frozen=True)
class Notification:
    code: int
    field: str
    message: str


class NotificationContext:
    def __init__(self) -> None:
        self._notifications: list[Notification] = []

    def add(self, code: int, field: str, message: str) -> None:
        self._notifications.append(Notification(code, field, message))

    def has_errors(self) -> bool:
        return len(self._notifications) > 0

    def raise_if_any(self) -> None:
        if self._notifications:
            raise ValidationNotificationError(list(self._notifications))


class ValidationNotificationError(AppException):
    code = 9400
    http_status = 400
    message = "Um ou mais campos são inválidos."

    def __init__(self, notifications: list[Notification]) -> None:
        self.notifications = notifications
        super().__init__(self.message)
