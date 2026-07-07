# -*- coding: utf-8 -*-
"""
Configurações globais do sistema de indicadores municipais.

Centraliza todas as constantes, caminhos e parâmetros configuráveis
do sistema, seguindo o princípio de Single Source of Truth.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env (se existir)
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Configurações imutáveis do sistema."""

    # === Diretórios ===
    BASE_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)

    @property
    def DATA_DIR(self) -> Path:
        """Diretório para dados baixados e cache."""
        path = self.BASE_DIR / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def CACHE_DIR(self) -> Path:
        """Diretório de cache para evitar re-downloads."""
        path = self.DATA_DIR / "cache"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def LOGS_DIR(self) -> Path:
        """Diretório de logs de execução."""
        path = self.BASE_DIR / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def TEMPLATES_DIR(self) -> Path:
        """Diretório de templates."""
        return self.BASE_DIR / "templates"

    @property
    def OUTPUT_DIR(self) -> Path:
        """Diretório de saída para planilhas geradas."""
        path = self.BASE_DIR / "output"
        path.mkdir(parents=True, exist_ok=True)
        return path

    # === Período de Análise ===
    ANOS_ANALISE: List[int] = field(default_factory=lambda: [2020, 2021, 2022, 2023, 2024, 2025])
    ANO_BASE: int = 2020

    # === Rede / Timeouts ===
    REQUEST_TIMEOUT: int = 60  # segundos
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 2.0  # segundos entre retries
    FTP_TIMEOUT: int = 120  # segundos para conexões FTP

    # === Cache ===
    CACHE_ENABLED: bool = True
    CACHE_TTL_HOURS: int = 24  # tempo de vida do cache em horas

    # === Logging ===
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    LOG_FORMAT: str = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    # === Comparações de Referência (Indicador 7) ===
    PERCENTUAL_ETP_BRASIL: float = 11.0  # % de alunos ETP no Brasil
    PERCENTUAL_ETP_OCDE: float = 37.0    # % de alunos ETP na OCDE

    # === Formatação Excel ===
    DECIMAL_PLACES: int = 2
    CURRENCY_SYMBOL: str = "R$"

    # === Playwright ===
    HEADLESS_BROWSER: bool = True
    BROWSER_TIMEOUT: int = 30000  # milissegundos


# Instância global de configurações
settings = Settings()
