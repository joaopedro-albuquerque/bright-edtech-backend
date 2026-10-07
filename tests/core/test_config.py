import importlib
import os

import pytest

from app.core import config as config_module


@pytest.fixture
def reload_config():
    original_env = os.environ.copy()

    def _reload(overrides: dict):
        for key, value in overrides.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        return importlib.reload(config_module)

    yield _reload

    os.environ.clear()
    os.environ.update(original_env)
    importlib.reload(config_module)


def test_settings_usa_valores_default_quando_env_vars_nao_definidas(reload_config):
    reloaded = reload_config({
        "AWS_REGION": None,
        "S3_BUCKET_NAME": None,
        "LOG_LEVEL": None,
        "BEDROCK_REGION": None,
        "BEDROCK_MODEL_SUMMARY": None,
        "BEDROCK_MODEL_EXTRACT": None,
    })

    assert reloaded.settings.aws_region == "us-east-1"
    assert reloaded.settings.s3_bucket_name is None
    assert reloaded.settings.log_level == "INFO"
    assert reloaded.settings.bedrock_region == "us-east-1"
    assert reloaded.settings.bedrock_model_summary == "anthropic.claude-3-5-sonnet-20241022-v2:0"
    assert reloaded.settings.bedrock_model_extract == "anthropic.claude-3-5-haiku-20241022-v1:0"


def test_settings_usa_valores_das_env_vars_quando_definidas(reload_config):
    reloaded = reload_config({
        "AWS_REGION": "sa-east-1",
        "S3_BUCKET_NAME": "meu-bucket",
        "LOG_LEVEL": "DEBUG",
        "BEDROCK_REGION": "us-west-2",
    })

    assert reloaded.settings.aws_region == "sa-east-1"
    assert reloaded.settings.s3_bucket_name == "meu-bucket"
    assert reloaded.settings.log_level == "DEBUG"
    assert reloaded.settings.bedrock_region == "us-west-2"


def test_bedrock_region_cai_para_aws_region_quando_nao_definido_explicitamente(reload_config):
    reloaded = reload_config({
        "AWS_REGION": "eu-west-1",
        "BEDROCK_REGION": None,
    })

    assert reloaded.settings.bedrock_region == "eu-west-1"


def test_termos_de_uso_versao_e_constante_fixa():
    assert config_module.TERMOS_DE_USO_VERSAO == "1.0"
