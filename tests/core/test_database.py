from botocore.exceptions import ClientError

from app.core import database as database_module


def _client_error():
    return ClientError({"Error": {"Code": "AccessDenied", "Message": "nope"}}, "GetParametersByPath")


def test_carregar_credenciais_rds_usa_ssm_quando_disponivel_e_completo(mocker):
    mock_boto_client = mocker.patch("app.core.database.boto3.client")
    mock_boto_client.return_value.get_parameters_by_path.return_value = {
        "Parameters": [
            {"Name": "/brightedtech/rds/db_host", "Value": "ssm-host"},
            {"Name": "/brightedtech/rds/db_user", "Value": "ssm-user"},
            {"Name": "/brightedtech/rds/db_password", "Value": "ssm-pass"},
        ]
    }

    resultado = database_module._carregar_credenciais_rds()

    assert resultado == {"db_host": "ssm-host", "db_user": "ssm-user", "db_password": "ssm-pass"}


def test_carregar_credenciais_rds_cai_para_env_quando_ssm_lanca_client_error(mocker, monkeypatch):
    mocker.patch("app.core.database.boto3.client", side_effect=_client_error())
    monkeypatch.setenv("DB_HOST", "env-host")
    monkeypatch.setenv("DB_USER", "env-user")
    monkeypatch.setenv("DB_PASSWORD", "env-pass")

    resultado = database_module._carregar_credenciais_rds()

    assert resultado == {"db_host": "env-host", "db_user": "env-user", "db_password": "env-pass"}


def test_carregar_credenciais_rds_cai_para_env_quando_ssm_retorna_parametros_incompletos(mocker, monkeypatch):
    mock_boto_client = mocker.patch("app.core.database.boto3.client")
    mock_boto_client.return_value.get_parameters_by_path.return_value = {
        "Parameters": [{"Name": "/brightedtech/rds/db_host", "Value": "ssm-host"}]
    }
    monkeypatch.setenv("DB_HOST", "env-host")
    monkeypatch.setenv("DB_USER", "env-user")
    monkeypatch.setenv("DB_PASSWORD", "env-pass")

    resultado = database_module._carregar_credenciais_rds()

    assert resultado == {"db_host": "env-host", "db_user": "env-user", "db_password": "env-pass"}


def test_carregar_credenciais_rds_usa_defaults_quando_nada_configurado(mocker, monkeypatch):
    mocker.patch("app.core.database.boto3.client", side_effect=_client_error())
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    resultado = database_module._carregar_credenciais_rds()

    assert resultado == {"db_host": "localhost", "db_user": "api_brightedtech", "db_password": None}


def test_get_db_connection_usa_credenciais_carregadas_e_db_name_do_env(mocker, monkeypatch):
    monkeypatch.setattr(database_module, "_CREDENCIAIS_RDS", {
        "db_host": "host-x", "db_user": "user-x", "db_password": "pass-x",
    })
    monkeypatch.setenv("DB_NAME", "banco-teste")
    mock_connect = mocker.patch("app.core.database.psycopg2.connect")

    database_module.get_db_connection()

    _, kwargs = mock_connect.call_args
    assert kwargs["host"] == "host-x"
    assert kwargs["database"] == "banco-teste"
    assert kwargs["user"] == "user-x"
    assert kwargs["password"] == "pass-x"


def test_get_db_connection_usa_db_name_default_quando_env_nao_definida(mocker, monkeypatch):
    monkeypatch.setattr(database_module, "_CREDENCIAIS_RDS", {"db_host": "h", "db_user": "u", "db_password": "p"})
    monkeypatch.delenv("DB_NAME", raising=False)
    mock_connect = mocker.patch("app.core.database.psycopg2.connect")

    database_module.get_db_connection()

    _, kwargs = mock_connect.call_args
    assert kwargs["database"] == "brightedtech"
