# -*- coding: utf-8 -*-
"""
Serviço de coleta de dados do QEdu / INEP.

Coleta número de escolas e matrículas (Ensino Médio e ETP).
"""

from typing import Dict, List

from config.settings import settings
from config.sources import data_sources
from models.indicators import EducacaoData, YearlyRecord
from services.base_service import BaseService


class QEduService(BaseService):
    """
    Serviço para coleta de dados de Educação.
    """

    def __init__(self) -> None:
        super().__init__("QEduService")

    def coletar(self, codigo_ibge: str, anos: List[int]) -> EducacaoData:
        """
        Coleta dados de educação para o município.

        Args:
            codigo_ibge: Código IBGE de 7 dígitos.
            anos: Anos a coletar.

        Returns:
            Dados EducacaoData.
        """
        self.logger.info(
            f"Iniciando coleta Educação para município {codigo_ibge}, anos {anos}"
        )

        cache_key = f"qedu_{codigo_ibge}_{'_'.join(map(str, anos))}"
        cached = self._read_cache(cache_key)
        if cached:
            return self._dict_to_educacao_data(cached)

        data = EducacaoData()

        # Extração de dados da API do QEdu / INEP
        for ano in anos:
            try:
                # Mock / Fallback - a API pública do QEdu foi desativada ou requer token
                # Extrair os microdados do INEP de 1GB por ano dinamicamente falharia
                # TODO: Implementar parser de CSV estático ou scraper
                
                data.escolas_ensino_medio.append(YearlyRecord(
                    ano=ano, disponivel=False,
                    observacao="API direta indisponível. Microdados não carregados.",
                    fonte="QEdu / INEP"
                ))
                data.escolas_tecnicas.append(YearlyRecord(
                    ano=ano, disponivel=False,
                    observacao="API direta indisponível",
                    fonte="QEdu / INEP"
                ))
                data.matriculas_ensino_medio.append(YearlyRecord(
                    ano=ano, disponivel=False,
                    observacao="API direta indisponível",
                    fonte="QEdu / INEP"
                ))
                data.matriculas_etp.append(YearlyRecord(
                    ano=ano, disponivel=False,
                    observacao="API direta indisponível",
                    fonte="QEdu / INEP"
                ))
            except Exception as e:
                self.logger.error(f"Erro ao coletar dados de educação para {ano}: {e}")

        self._write_cache(cache_key, self._educacao_data_to_dict(data))
        return data

    # === Serialização ===

    @staticmethod
    def _educacao_data_to_dict(data: EducacaoData) -> Dict:
        return data.to_dict()

    @staticmethod
    def _dict_to_educacao_data(d: Dict) -> EducacaoData:
        data = EducacaoData()
        for field_name in ["escolas_tecnicas", "escolas_ensino_medio", "matriculas_etp", "matriculas_ensino_medio"]:
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
