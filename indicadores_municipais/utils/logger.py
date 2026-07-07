# -*- coding: utf-8 -*-
"""
Sistema de logging estruturado.

Configura logs para arquivo e console com formatação padronizada.
Cada execução gera um arquivo de log próprio com timestamp.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import settings


_initialized: bool = False


def setup_logger(
    name: str = "indicadores_municipais",
    log_dir: Optional[Path] = None,
) -> logging.Logger:
    """
    Configura o logger raiz da aplicação.

    Cria handlers para console (stdout) e arquivo de log.
    Chamado uma única vez no início da execução.

    Args:
        name: Nome do logger raiz.
        log_dir: Diretório para salvar logs. Usa settings.LOGS_DIR se None.

    Returns:
        Logger configurado.
    """
    global _initialized

    logger = logging.getLogger(name)

    if _initialized:
        return logger

    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    formatter = logging.Formatter(
        fmt=settings.LOG_FORMAT,
        datefmt=settings.LOG_DATE_FORMAT,
    )

    # Handler: Console (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler: Arquivo de log
    if log_dir is None:
        log_dir = settings.LOGS_DIR

    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"execucao_{timestamp}.log"

    file_handler = logging.FileHandler(
        filename=str(log_file),
        encoding="utf-8",
        mode="w",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _initialized = True
    logger.info(f"Logger inicializado. Arquivo de log: {log_file}")

    return logger


def get_logger(agent_name: str) -> logging.Logger:
    """
    Retorna um logger filho para um agente ou serviço específico.

    Args:
        agent_name: Nome do agente/serviço (ex: 'ExcelReader', 'CAGEDService').

    Returns:
        Logger nomeado como filho do logger raiz.
    """
    return logging.getLogger(f"indicadores_municipais.{agent_name}")
