# -*- coding: utf-8 -*-
"""
Validadores de dados coletados.

Verifica integridade, tipos e ranges dos dados
coletados pelos serviços antes de prosseguir com a análise.
"""

from typing import Any, Dict, List, Optional, Tuple

from models.indicators import CollectedData, YearlyRecord
from utils.logger import get_logger

logger = get_logger("DataValidator")


class DataValidator:
    """Validador de dados coletados das fontes oficiais."""

    @staticmethod
    def validate_yearly_records(
        records: List[YearlyRecord],
        field_name: str,
        expected_years: List[int],
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Valida uma lista de registros anuais.

        Args:
            records: Lista de YearlyRecord a validar.
            field_name: Nome do campo (para mensagens de erro).
            expected_years: Anos esperados.
            min_value: Valor mínimo aceitável (se aplicável).
            max_value: Valor máximo aceitável (se aplicável).

        Returns:
            Tupla (válido, lista_de_avisos).
        """
        warnings: List[str] = []
        valid = True

        # Verificar anos faltantes
        years_present = {r.ano for r in records if r.disponivel}
        years_missing = set(expected_years) - years_present

        if years_missing:
            warnings.append(
                f"{field_name}: dados faltantes para os anos {sorted(years_missing)}"
            )

        # Verificar valores
        for record in records:
            if not record.disponivel:
                continue

            if record.valor is None:
                warnings.append(
                    f"{field_name} ({record.ano}): valor nulo"
                )
                continue

            if min_value is not None and record.valor < min_value:
                warnings.append(
                    f"{field_name} ({record.ano}): valor {record.valor} "
                    f"abaixo do mínimo esperado ({min_value})"
                )

            if max_value is not None and record.valor > max_value:
                warnings.append(
                    f"{field_name} ({record.ano}): valor {record.valor} "
                    f"acima do máximo esperado ({max_value})"
                )

        return valid, warnings

    @classmethod
    def validate_collected_data(
        cls,
        data: CollectedData,
        expected_years: List[int],
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Valida todos os dados coletados.

        Args:
            data: Dados consolidados.
            expected_years: Anos esperados.

        Returns:
            Tupla (válido, erros, avisos).
        """
        errors: List[str] = []
        warnings: List[str] = []

        # === Validar CAGED ===
        if not data.caged.saldo:
            errors.append("CAGED: nenhum dado de saldo de empregos coletado")
        else:
            _, w = cls.validate_yearly_records(
                data.caged.admissoes, "CAGED Admissões", expected_years, min_value=0
            )
            warnings.extend(w)

            _, w = cls.validate_yearly_records(
                data.caged.desligamentos, "CAGED Desligamentos", expected_years, min_value=0
            )
            warnings.extend(w)

            _, w = cls.validate_yearly_records(
                data.caged.estoque, "CAGED Estoque", expected_years, min_value=0
            )
            warnings.extend(w)

        # === Validar IBGE ===
        if not data.ibge.populacao:
            errors.append("IBGE: nenhum dado de população coletado")
        else:
            _, w = cls.validate_yearly_records(
                data.ibge.populacao, "IBGE População", expected_years,
                min_value=100,  # Mínimo razoável para qualquer município
                max_value=15_000_000,  # São Paulo ~12M
            )
            warnings.extend(w)

        if not data.ibge.salario_medio:
            warnings.append("IBGE: nenhum dado de salário médio coletado")
        else:
            _, w = cls.validate_yearly_records(
                data.ibge.salario_medio, "IBGE Salário Médio", expected_years,
                min_value=500,
                max_value=50_000,
            )
            warnings.extend(w)

        # === Validar Empresas ===
        if not data.empresas.empresas_abertas:
            warnings.append("Empresas: nenhum dado de empresas abertas coletado")
        else:
            _, w = cls.validate_yearly_records(
                data.empresas.empresas_abertas, "Empresas Abertas", expected_years,
                min_value=0,
            )
            warnings.extend(w)

        if not data.empresas.tempo_medio_abertura:
            warnings.append("Empresas: nenhum dado de tempo de abertura coletado")
        else:
            _, w = cls.validate_yearly_records(
                data.empresas.tempo_medio_abertura, "Tempo Abertura", expected_years,
                min_value=0,
                max_value=365,  # Máximo razoável de 1 ano
            )
            warnings.extend(w)

        # === Validar Educação ===
        if not data.educacao.escolas_tecnicas:
            warnings.append("Educação: nenhum dado de escolas técnicas coletado")

        if not data.educacao.matriculas_ensino_medio:
            warnings.append("Educação: nenhum dado de matrículas ensino médio coletado")

        # Resultado geral
        is_valid = len(errors) == 0

        for e in errors:
            logger.error(f"Validação: {e}")
        for w in warnings:
            logger.warning(f"Validação: {w}")

        if is_valid:
            logger.info("Validação dos dados coletados: OK")
        else:
            logger.error(
                f"Validação falhou: {len(errors)} erro(s), {len(warnings)} aviso(s)"
            )

        return is_valid, errors, warnings

    @staticmethod
    def validate_municipality_name(name: str) -> bool:
        """
        Valida se o nome do município parece válido.

        Args:
            name: Nome a validar.

        Returns:
            True se o nome é válido.
        """
        if not name or not name.strip():
            return False
        if len(name.strip()) < 2:
            return False
        if name.strip().isdigit():
            return False
        return True
