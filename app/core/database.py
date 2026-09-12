import logging
import os

import boto3
import psycopg2
import psycopg2.extras
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# Carrega variáveis locais (usadas como fallback se o SSM não estiver acessível)
load_dotenv()
psycopg2.extras.register_uuid()


def _carregar_credenciais_rds() -> dict:
    """Busca host/user/password do SSM Parameter Store (/brightedtech/rds/).
    Executado uma única vez, na primeira conexão (não a cada request).
    Cai pro .env/variáveis de ambiente se o SSM não estiver acessível (dev local sem AWS)."""
    try:
        region = os.getenv("AWS_REGION", "us-east-1")
        ssm_client = boto3.client("ssm", region_name=region)
        response = ssm_client.get_parameters_by_path(
            Path="/brightedtech/rds/",
            WithDecryption=True,
        )
        credenciais = {
            param["Name"].split("/")[-1]: param["Value"]
            for param in response["Parameters"]
        }
        if credenciais.get("db_host") and credenciais.get("db_user") and credenciais.get("db_password"):
            logger.info("Credenciais do RDS carregadas do SSM Parameter Store.")
            return credenciais
    except (BotoCoreError, ClientError) as exc:
        logger.warning(f"Não foi possível carregar credenciais do SSM, usando fallback de variáveis de ambiente: {exc}")

    return {
        "db_host": os.getenv("DB_HOST", "localhost"),
        "db_user": os.getenv("DB_USER", "api_brightedtech"),
        "db_password": os.getenv("DB_PASSWORD"),
    }


_CREDENCIAIS_RDS = _carregar_credenciais_rds()


def get_db_connection():
    db_name = os.getenv("DB_NAME", "brightedtech")

    return psycopg2.connect(
        host=_CREDENCIAIS_RDS["db_host"],
        database=db_name,
        user=_CREDENCIAIS_RDS["db_user"],
        password=_CREDENCIAIS_RDS["db_password"],
        cursor_factory=RealDictCursor
    )
