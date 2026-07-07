# -*- coding: utf-8 -*-
"""
Resolução de códigos IBGE para municípios.

Realiza busca fuzzy de nomes de municípios e resolve
para códigos IBGE de 7 dígitos usando a API IBGE Localidades.
"""

import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

from config.settings import settings
from config.sources import data_sources
from utils.logger import get_logger

logger = get_logger("IBGECodeResolver")


class IBGECodeResolver:
    """
    Resolve nomes de municípios para códigos IBGE.

    Usa cache local para evitar chamadas repetidas à API.
    Busca fuzzy permite encontrar municípios mesmo com pequenas
    variações na grafia.
    """

    def __init__(self) -> None:
        self._cache_file = settings.CACHE_DIR / "municipios_ibge.json"
        self._municipios: Dict[str, Dict] = {}
        self._load_cache()

    def _normalize(self, text: str) -> str:
        """
        Normaliza texto para comparação fuzzy.

        Remove acentos, converte para minúsculas e remove
        caracteres especiais.

        Args:
            text: Texto a normalizar.

        Returns:
            Texto normalizado.
        """
        # Remove acentos
        text = unicodedata.normalize("NFKD", text)
        text = "".join(c for c in text if not unicodedata.combining(c))
        # Minúsculas e remove caracteres especiais
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def _load_cache(self) -> None:
        """Carrega cache local de municípios."""
        if self._cache_file.exists():
            try:
                with open(self._cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._municipios = {
                        self._normalize(k): v for k, v in data.items()
                    }
                logger.debug(f"Cache carregado: {len(self._municipios)} municípios")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Erro ao carregar cache: {e}")
                self._municipios = {}

    def _save_cache(self) -> None:
        """Salva cache local de municípios."""
        try:
            # Salvar com nomes originais (não normalizados)
            data = {}
            for info in self._municipios.values():
                data[info["nome"]] = info

            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Cache salvo: {len(data)} municípios")
        except IOError as e:
            logger.warning(f"Erro ao salvar cache: {e}")

    def _fetch_all_municipios(self) -> None:
        """
        Busca todos os municípios da API IBGE Localidades.

        Popula o cache interno com código IBGE, nome e UF.
        """
        url = f"{data_sources.ibge.LOCALIDADES_URL}{data_sources.ibge.MUNICIPIOS_ENDPOINT}"
        logger.info("Buscando lista de municípios na API IBGE...")

        try:
            response = requests.get(
                url,
                timeout=settings.REQUEST_TIMEOUT,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            municipios = response.json()

            for m in municipios:
                nome = m["nome"]
                uf = m["microrregiao"]["mesorregiao"]["UF"]["sigla"]
                codigo = str(m["id"])

                info = {
                    "nome": nome,
                    "estado": uf,
                    "codigo_ibge": codigo,
                    "codigo_ibge_6": codigo[:6],  # Código de 6 dígitos (usado no CAGED)
                }

                key = self._normalize(nome)
                self._municipios[key] = info

                # Também indexar com UF para desambiguação
                key_with_uf = self._normalize(f"{nome} {uf}")
                self._municipios[key_with_uf] = info

            logger.info(f"Carregados {len(municipios)} municípios da API IBGE")
            self._save_cache()

        except requests.RequestException as e:
            logger.error(f"Erro ao buscar municípios do IBGE: {e}")
            raise RuntimeError(f"Não foi possível carregar lista de municípios: {e}")

    def resolver(
        self, nome_municipio: str, estado: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Resolve nome de município para código IBGE.

        Args:
            nome_municipio: Nome do município (aceita variações).
            estado: Sigla do estado (opcional, para desambiguação).

        Returns:
            Dicionário com nome, estado e código IBGE, ou None.
        """
        # Carregar municípios se cache vazio
        if not self._municipios:
            self._fetch_all_municipios()

        # Tentar match exato primeiro
        key = self._normalize(nome_municipio)
        if key in self._municipios:
            result = self._municipios[key]
            if estado and result["estado"] != estado.upper():
                # Tentar com UF
                key_uf = self._normalize(f"{nome_municipio} {estado}")
                if key_uf in self._municipios:
                    return self._municipios[key_uf]
            return result

        # Se estado fornecido, tentar com UF
        if estado:
            key_uf = self._normalize(f"{nome_municipio} {estado}")
            if key_uf in self._municipios:
                return self._municipios[key_uf]

        # Busca fuzzy: encontrar melhor match
        best_match = self._fuzzy_search(key, estado)
        if best_match:
            return best_match

        logger.warning(f"Município não encontrado: '{nome_municipio}' (UF: {estado})")
        return None

    def _fuzzy_search(
        self, normalized_name: str, estado: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Busca fuzzy por nome de município.

        Usa similaridade de substring para encontrar matches parciais.

        Args:
            normalized_name: Nome normalizado do município.
            estado: Sigla do estado (para filtrar resultados).

        Returns:
            Melhor match encontrado ou None.
        """
        best_score = 0.0
        best_match = None

        for key, info in self._municipios.items():
            # Filtrar por estado se fornecido
            if estado and info["estado"] != estado.upper():
                continue

            # Calcular similaridade simples
            score = self._similarity(normalized_name, key)
            if score > best_score and score > 0.75:  # Threshold mínimo
                best_score = score
                best_match = info

        if best_match:
            logger.info(
                f"Match fuzzy: '{normalized_name}' → '{best_match['nome']}' "
                f"(score: {best_score:.2f})"
            )

        return best_match

    @staticmethod
    def _similarity(s1: str, s2: str) -> float:
        """
        Calcula similaridade entre duas strings (coeficiente de Dice).

        Args:
            s1: Primeira string.
            s2: Segunda string.

        Returns:
            Score de similaridade entre 0.0 e 1.0.
        """
        if not s1 or not s2:
            return 0.0

        if s1 == s2:
            return 1.0

        # Bigrams
        bigrams1 = set(s1[i : i + 2] for i in range(len(s1) - 1))
        bigrams2 = set(s2[i : i + 2] for i in range(len(s2) - 1))

        if not bigrams1 or not bigrams2:
            return 0.0

        intersection = bigrams1 & bigrams2
        return 2.0 * len(intersection) / (len(bigrams1) + len(bigrams2))

    def get_estado_from_municipio(self, nome_municipio: str) -> Optional[str]:
        """
        Infere o estado a partir do nome do município.

        Args:
            nome_municipio: Nome do município.

        Returns:
            Sigla do estado ou None.
        """
        result = self.resolver(nome_municipio)
        if result:
            return result["estado"]
        return None
