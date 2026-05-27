import os
import boto3
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Carrega variáveis locais (ignoradas em ambiente de nuvem nativo)
load_dotenv()

def get_db_connection():
    region = os.getenv("AWS_REGION", "us-east-1")
    systemManager_client = boto3.client('ssm', region_name=region)

    response = systemManager_client.get_parameters_by_path(
        Path='/brightedtech/rds/',
        WithDecryption=True
    )
    
    credenciais = {
        param['Name'].split('/')[-1]: param['Value'] 
        for param in response['Parameters']
    }
    
    db_user = credenciais.get('db_user')
    db_password = credenciais.get('db_password')
    db_host = os.getenv("DB_HOST", "localhost")
    db_name = os.getenv("DB_NAME", "brightedtech")
    
    return psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password,
        cursor_factory=RealDictCursor
    )