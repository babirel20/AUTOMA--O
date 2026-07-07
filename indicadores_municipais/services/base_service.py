# -*- coding: utf-8 -*-
"""
Classe base para todos os serviços de coleta.

Define a interface padrão e funcionalidades comuns como
retry, cache e tratamento de erros.
"""

import hashlib
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from config.settings import settings
from utils.logger import get_logger


class BaseService(ABC):
    """
    Classe base abstrata para serviços de coleta de dados.

    Implementa funcionalidades compartilhadas:
    - Retry com backoff exponencial
    - Cache de respostas
    - Tratamento padronizado de erros
    - Logging estruturado
    """

    def __init__(self, service_name: str) -> None:
        """
        Inicializa o serviço base.

        Args:
            service_name: Nome do serviço para logging.
        """
        self.service_name = service_name
        self.logger = get_logger(service_name)
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "IndicadoresMunicipais/1.0 (Trabalho Acadêmico)",
            "Accept": "application/json",
        })

    @abstractmethod
    def coletar(
        self, codigo_ibge: str, anos: List[int]
    ) -> Any:
        """
        Método principal de coleta de dados.

        Args:
            codigo_ibge: Código IBGE de 7 dígitos do município.
            anos: Lista de anos a coletar.

        Returns:
            Dados coletados (tipo específico de cada serviço).
        """
        ...

    def _request_with_retry(
        self,
        url: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[int] = None,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Realiza requisição HTTP com retry e backoff exponencial.

        Args:
            url: URL da requisição.
            method: Método HTTP (GET, POST, etc).
            params: Parâmetros da query string.
            headers: Headers adicionais.
            timeout: Timeout em segundos (usa padrão se None).

        Returns:
            Response da requisição.

        Raises:
            requests.RequestException: Se todas as tentativas falharem.
        """
        if timeout is None:
            timeout = settings.REQUEST_TIMEOUT

        last_exception: Optional[Exception] = None

        for attempt in range(1, settings.MAX_RETRIES + 1):
            try:
                self.logger.debug(
                    f"Requisição {method} {url} (tentativa {attempt}/{settings.MAX_RETRIES})"
                )

                response = self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                    timeout=timeout,
                    **kwargs,
                )
                response.raise_for_status()

                self.logger.debug(
                    f"Resposta OK: {response.status_code} ({len(response.content)} bytes)"
                )
                return response

            except requests.RequestException as e:
                last_exception = e
                self.logger.warning(
                    f"Tentativa {attempt} falhou: {type(e).__name__}: {e}"
                )

                if attempt < settings.MAX_RETRIES:
                    delay = settings.RETRY_DELAY * (2 ** (attempt - 1))
                    self.logger.info(f"Aguardando {delay:.1f}s antes da próxima tentativa...")
                    time.sleep(delay)

        raise requests.RequestException(
            f"Todas as {settings.MAX_RETRIES} tentativas falharam para {url}. "
            f"Último erro: {last_exception}"
        )

    def _get_cache_path(self, cache_key: str) -> Path:
        """
        Gera o caminho do arquivo de cache para uma chave.

        Args:
            cache_key: Chave única do cache.

        Returns:
            Path do arquivo de cache.
        """
        safe_key = hashlib.md5(cache_key.encode()).hexdigest()
        return settings.CACHE_DIR / f"{self.service_name}_{safe_key}.json"

    def _read_cache(self, cache_key: str) -> Optional[Any]:
        """
        Lê dados do cache local.

        Args:
            cache_key: Chave do cache.

        Returns:
            Dados do cache ou None se expirado/inexistente.
        """
        if not settings.CACHE_ENABLED:
            return None

        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)

            # Verificar TTL
            cached_at = datetime.fromisoformat(cached.get("cached_at", "2000-01-01"))
            ttl = timedelta(hours=settings.CACHE_TTL_HOURS)

            if datetime.now() - cached_at > ttl:
                self.logger.debug(f"Cache expirado para '{cache_key}'")
                return None

            self.logger.debug(f"Cache hit para '{cache_key}'")
            return cached.get("data")

        except (json.JSONDecodeError, IOError, KeyError) as e:
            self.logger.warning(f"Erro ao ler cache '{cache_key}': {e}")
            return None

    def _write_cache(self, cache_key: str, data: Any) -> None:
        """
        Salva dados no cache local.

        Args:
            cache_key: Chave do cache.
            data: Dados a cachear.
        """
        if not settings.CACHE_ENABLED:
            return

        cache_path = self._get_cache_path(cache_key)

        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "cached_at": datetime.now().isoformat(),
                        "cache_key": cache_key,
                        "service": self.service_name,
                        "data": data,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            self.logger.debug(f"Cache salvo para '{cache_key}'")
        except IOError as e:
            self.logger.warning(f"Erro ao salvar cache '{cache_key}': {e}")

    def __del__(self) -> None:
        """Fecha a sessão HTTP ao destruir o serviço."""
        try:
            self._session.close()
        except Exception:
            pass
