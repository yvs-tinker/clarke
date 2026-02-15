"""Centralised application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from dotenv import load_dotenv
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application settings schema loaded from environment variables.

    Params:
        None: Values are read from process environment and optional `.env` file.
    Returns:
        Settings: Parsed and validated settings object.
    """

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    MEDASR_MODEL_ID: str = "google/medasr"
    MEDGEMMA_4B_MODEL_ID: str = "google/medgemma-1.5-4b-it"
    MEDGEMMA_27B_MODEL_ID: str = "google/medgemma-27b-text-it"
    HF_TOKEN: str = ""
    QUANTIZE_4BIT: bool = True
    USE_FLASH_ATTENTION: bool = True

    FHIR_SERVER_URL: str = "http://localhost:8080/fhir"
    USE_MOCK_FHIR: bool = True
    FHIR_TIMEOUT_S: int = 10

    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 7860
    LOG_LEVEL: str = "INFO"
    MAX_AUDIO_DURATION_S: int = 1800
    PIPELINE_TIMEOUT_S: int = 120
    DOC_GEN_MAX_TOKENS: int = 2048
    DOC_GEN_TEMPERATURE: float = 0.3

    WANDB_API_KEY: str = ""
    WANDB_PROJECT: str = "clarke-finetuning"
    LORA_RANK: int = 16
    LORA_ALPHA: int = 32
    LORA_DROPOUT: float = 0.05
    TRAINING_EPOCHS: int = 3
    LEARNING_RATE: float = 2e-4
    BATCH_SIZE: int = 2
    GRAD_ACCUM_STEPS: int = 8
    MAX_SEQ_LENGTH: int = 4096


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance for process-wide reuse.

    Params:
        None: Reads values from environment variables and `.env` if present.
    Returns:
        Settings: Cached configuration object.
    """

    return Settings()
