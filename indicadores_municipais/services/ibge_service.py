# -*- coding: utf-8 -*-
"""
Serviço de coleta de dados do IBGE.

Coleta população estimada e salário médio mensal
via API SIDRA e IBGE Cidades.
"""

from typing import Dict, List

import pandas as pd
import requests

from config.settings import settings
from config.sources import data_sources
from models.indicators import IBGEData, YearlyRecord
from services.base_service import BaseService


class IBGEService(BaseService):
    """
    Serviço para coleta de dados do IBGE.
    """

    def __init__(self) -> None:
        super().__init__("IBGEService")

    def coletar(self, codigo_ibge: str, anos: List[int]) -> IBGEData:
        """
        Coleta dados do IBGE para o município.

        Args:
            codigo_ibge: Código IBGE de 7 dígitos.
            anos: Anos a coletar.

        Returns:
            Dados IBGE com população e salário médio.
        """
        self.logger.info(
            f"Iniciando coleta IBGE para município {codigo_ibge}, anos {anos}"
        )

        # Verificar cache
        cache_key = f"ibge_{codigo_ibge}_{'_'.join(map(str, anos))}"
        cached = self._read_cache(cache_key)
        if cached:
            return self._dict_to_ibge_data(cached)

        data = IBGEData()

        # Coletar População
        self._coletar_populacao(codigo_ibge, anos, data)

        # Coletar Salário Médio
        self._coletar_salario(codigo_ibge, anos, data)

        # Salvar cache
        self._write_cache(cache_key, self._ibge_data_to_dict(data))

        return data

    def _coletar_populacao(self, codigo_ibge: str, anos: List[int], data: IBGEData) -> None:
        """Coleta população estimada via API SIDRA (Tabela 6579)."""
        # Formatar período: ex: "2020,2021"
        periodo = ",".join(str(ano) for ano in anos)
        
        tabela = data_sources.ibge.TABELA_POPULACAO
        variavel = data_sources.ibge.VARIAVEL_POPULACAO
        nivel = data_sources.ibge.NIVEL_MUNICIPAL
        
        # URL da API SIDRA
        url = f"{data_sources.ibge.SIDRA_URL}/t/{tabela}/n{nivel}/{codigo_ibge}/v/{variavel}/p/{periodo}"
        
        try:
            response = self._request_with_retry(url)
            json_data = response.json()
            
            # Formato SIDRA: a primeira linha é o cabeçalho, os dados vêm depois
            if isinstance(json_data, list) and len(json_data) > 1:
                for row in json_data[1:]:
                    ano_str = row.get("D3C") or row.get("D2C") # Geralmente o período está aqui
                    if ano_str and len(str(ano_str)) >= 4:
                        ano = int(str(ano_str)[:4])
                        if ano in anos:
                            valor = row.get("V")
                            if valor and valor != "..." and valor != "-":
                                data.populacao.append(YearlyRecord(
                                    ano=ano,
                                    valor=float(valor),
                                    fonte="IBGE/SIDRA (Tab 6579)",
                                ))
        except Exception as e:
            self.logger.error(f"Erro ao coletar população do SIDRA: {e}")

        # Se faltou algum ano, marcar como não disponível
        anos_coletados = [r.ano for r in data.populacao]
        for ano in anos:
            if ano not in anos_coletados:
                data.populacao.append(YearlyRecord(
                    ano=ano,
                    disponivel=False,
                    observacao="População não disponível",
                    fonte="IBGE/SIDRA (Tab 6579)"
                ))

    def _coletar_salario(self, codigo_ibge: str, anos: List[int], data: IBGEData) -> None:
        """Coleta salário médio mensal via API SIDRA (Tabela 5938 - CEMPRE)."""
        periodo = ",".join(str(ano) for ano in anos)
        
        tabela = data_sources.ibge.TABELA_SALARIO
        variavel = data_sources.ibge.VARIAVEL_SALARIO
        nivel = data_sources.ibge.NIVEL_MUNICIPAL
        
        url = f"{data_sources.ibge.SIDRA_URL}/t/{tabela}/n{nivel}/{codigo_ibge}/v/{variavel}/p/{periodo}"
        
        try:
            response = self._request_with_retry(url)
            json_data = response.json()
            
            if isinstance(json_data, list) and len(json_data) > 1:
                for row in json_data[1:]:
                    ano_str = row.get("D3C") or row.get("D2C")
                    if ano_str and len(str(ano_str)) >= 4:
                        ano = int(str(ano_str)[:4])
                        if ano in anos:
                            valor = row.get("V")
                            if valor and valor != "..." and valor != "-":
                                try:
                                    valor_float = float(str(valor).replace(",", "."))
                                    data.salario_medio.append(YearlyRecord(
                                        ano=ano,
                                        valor=valor_float,
                                        fonte="IBGE/SIDRA (Tab 5938)",
                                    ))
                                except ValueError:
                                    pass
        except Exception as e:
            self.logger.error(f"Erro ao coletar salário médio do SIDRA: {e}")

        anos_coletados = [r.ano for r in data.salario_medio]
        for ano in anos:
            if ano not in anos_coletados:
                data.salario_medio.append(YearlyRecord(
                    ano=ano,
                    disponivel=False,
                    observacao="Salário médio não disponível",
                    fonte="IBGE/SIDRA (Tab 5938)"
                ))

    # === Serialização ===

    @staticmethod
    def _ibge_data_to_dict(data: IBGEData) -> Dict:
        """Converte IBGEData para dicionário (para cache)."""
        return data.to_dict()

    @staticmethod
    def _dict_to_ibge_data(d: Dict) -> IBGEData:
        """Converte dicionário do cache para IBGEData."""
        data = IBGEData()
        for field_name in ["populacao", "salario_medio"]:
            records = d.get(field_name, [])
            field_list = getattr(data, field_name)
            for r in records:
                field_list.append(YearlyRecord(
                    ano=r.get("ano", 0),
                    valor=r.get("valor"),
                    fonte=r.get("fonte", ""),
                    observacao=r.get("observacao", ""),
                    disponivel=r.get("disponivel", True),
                ))
        return data
