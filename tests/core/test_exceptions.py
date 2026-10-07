import pytest

from app.core.exceptions import (
    AiGenerationError,
    AppException,
    DashboardDatabaseError,
    DashboardError,
    DatabaseError,
    DocumentDatabaseError,
    DocumentError,
    DocumentNotFoundError,
    FlashcardDatabaseError,
    FlashcardError,
    FlashcardNotFoundError,
    InfrastructureError,
    Notification,
    NotificationContext,
    ProfileDatabaseError,
    ProfileError,
    ProfileNotFoundError,
    QuizDatabaseError,
    QuizError,
    QuizNotFoundError,
    ResumoDatabaseError,
    ResumoError,
    ResumoNotFoundError,
    RevisaoDatabaseError,
    RevisaoError,
    RevisaoNotFoundError,
    StorageError,
    UnexpectedError,
    ValidationNotificationError,
)


class TestAppException:
    def test_app_exception_usa_mensagem_customizada_quando_informada(self):
        exc = AppException("mensagem customizada")

        assert exc.message == "mensagem customizada"
        assert str(exc) == "mensagem customizada"

    def test_app_exception_usa_mensagem_padrao_quando_nao_informada(self):
        exc = AppException()

        assert exc.message == "Ocorreu um erro inesperado."
        assert exc.code == 9000
        assert exc.http_status == 500

    def test_app_exception_e_instancia_de_exception(self):
        exc = AppException("erro")

        assert isinstance(exc, Exception)


@pytest.mark.parametrize(
    "exc_class, expected_code, expected_status",
    [
        (InfrastructureError, 9000, 500),
        (DatabaseError, 9001, 500),
        (StorageError, 9002, 502),
        (AiGenerationError, 9003, 502),
        (UnexpectedError, 9999, 500),
        (DocumentError, 1000, 500),
        (DocumentNotFoundError, 1001, 404),
        (DocumentDatabaseError, 1002, 500),
        (ProfileError, 2000, 500),
        (ProfileNotFoundError, 2001, 404),
        (ProfileDatabaseError, 2002, 500),
        (FlashcardError, 3000, 500),
        (FlashcardNotFoundError, 3001, 404),
        (FlashcardDatabaseError, 3002, 500),
        (QuizError, 4000, 500),
        (QuizNotFoundError, 4001, 404),
        (QuizDatabaseError, 4002, 500),
        (ResumoError, 5000, 500),
        (ResumoNotFoundError, 5001, 404),
        (ResumoDatabaseError, 5002, 500),
        (RevisaoError, 6000, 500),
        (RevisaoNotFoundError, 6001, 404),
        (RevisaoDatabaseError, 6002, 500),
        (DashboardError, 7000, 500),
        (DashboardDatabaseError, 7001, 500),
    ],
)
def test_excecoes_de_dominio_tem_code_e_http_status_corretos(exc_class, expected_code, expected_status):
    exc = exc_class("mensagem qualquer")

    assert exc.code == expected_code
    assert exc.http_status == expected_status
    assert isinstance(exc, AppException)


@pytest.mark.parametrize(
    "exc_class, base_class",
    [
        (DatabaseError, InfrastructureError),
        (StorageError, InfrastructureError),
        (AiGenerationError, InfrastructureError),
        (DocumentNotFoundError, DocumentError),
        (DocumentDatabaseError, DocumentError),
        (ProfileNotFoundError, ProfileError),
        (FlashcardNotFoundError, FlashcardError),
        (QuizNotFoundError, QuizError),
        (ResumoNotFoundError, ResumoError),
        (RevisaoNotFoundError, RevisaoError),
        (DashboardDatabaseError, DashboardError),
    ],
)
def test_excecoes_especificas_herdam_da_base_do_dominio(exc_class, base_class):
    exc = exc_class("mensagem")

    assert isinstance(exc, base_class)


def test_excecao_sem_mensagem_customizada_usa_mensagem_default_da_classe():
    exc = DocumentNotFoundError()

    assert exc.message == "Documento ou pasta não encontrado."


class TestNotificationContext:
    def test_has_errors_retorna_false_quando_vazio(self):
        ctx = NotificationContext()

        assert ctx.has_errors() is False

    def test_has_errors_retorna_true_apos_add(self):
        ctx = NotificationContext()
        ctx.add(2101, "estilo_preferido", "Estilo inválido.")

        assert ctx.has_errors() is True

    def test_raise_if_any_nao_levanta_quando_vazio(self):
        ctx = NotificationContext()

        ctx.raise_if_any()

    def test_raise_if_any_levanta_validation_notification_error_com_notificacoes_acumuladas(self):
        ctx = NotificationContext()
        ctx.add(2101, "estilo_preferido", "Estilo inválido.")
        ctx.add(2102, "formato_preferido", "Formato inválido.")

        with pytest.raises(ValidationNotificationError) as exc_info:
            ctx.raise_if_any()

        notifications = exc_info.value.notifications
        assert len(notifications) == 2
        assert notifications[0] == Notification(2101, "estilo_preferido", "Estilo inválido.")
        assert notifications[1] == Notification(2102, "formato_preferido", "Formato inválido.")

    def test_validation_notification_error_tem_code_e_status_fixos(self):
        ctx = NotificationContext()
        ctx.add(1003, "documento", "Apenas PDF é permitido.")

        with pytest.raises(ValidationNotificationError) as exc_info:
            ctx.raise_if_any()

        assert exc_info.value.code == 9400
        assert exc_info.value.http_status == 400
        assert isinstance(exc_info.value, AppException)
