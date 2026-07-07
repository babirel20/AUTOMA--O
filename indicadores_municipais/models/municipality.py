# -*- coding: utf-8 -*-
"""
Modelos de dados para informações do município e mapeamento da planilha.

Define as estruturas que representam os dados extraídos da planilha
de entrada pelo Agente 1 (Leitor de Planilhas).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MunicipalityInfo:
    """Informações identificadas sobre o município analisado."""

    nome: str
    """Nome do município (ex: 'Belo Horizonte')."""

    estado: str
    """Sigla do estado (ex: 'MG')."""

    codigo_ibge: Optional[str] = None
    """Código IBGE de 7 dígitos do município."""

    anos: List[int] = field(default_factory=list)
    """Anos de análise identificados na planilha."""

    def __post_init__(self) -> None:
        """Normaliza o nome do município."""
        self.nome = self.nome.strip().title()
        self.estado = self.estado.strip().upper()

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            "municipio": self.nome,
            "estado": self.estado,
            "codigo_ibge": self.codigo_ibge,
            "anos": self.anos,
        }


@dataclass
class CellMapping:
    """Mapeamento de uma célula específica na planilha."""

    sheet_name: str
    """Nome da aba."""

    cell_reference: str
    """Referência da célula (ex: 'B5')."""

    row: int
    """Número da linha (1-indexed)."""

    col: int
    """Número da coluna (1-indexed)."""

    field_name: str
    """Nome do campo/indicador que esta célula representa."""

    year: Optional[int] = None
    """Ano associado a esta célula (se aplicável)."""

    current_value: Optional[Any] = None
    """Valor atual da célula (None se vazia)."""

    is_empty: bool = True
    """Se a célula está vazia e precisa ser preenchida."""

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            "aba": self.sheet_name,
            "celula": self.cell_reference,
            "linha": self.row,
            "coluna": self.col,
            "campo": self.field_name,
            "ano": self.year,
            "valor_atual": self.current_value,
            "vazia": self.is_empty,
        }


@dataclass
class SheetMapping:
    """Mapeamento de uma aba da planilha."""

    name: str
    """Nome da aba."""

    indicator_name: Optional[str] = None
    """Nome do indicador associado a esta aba."""

    header_row: int = 1
    """Linha do cabeçalho."""

    data_start_row: int = 2
    """Linha de início dos dados."""

    year_columns: Dict[int, int] = field(default_factory=dict)
    """Mapeamento ano → coluna."""

    cells: List[CellMapping] = field(default_factory=list)
    """Células mapeadas nesta aba."""

    def get_empty_cells(self) -> List[CellMapping]:
        """Retorna apenas as células vazias."""
        return [c for c in self.cells if c.is_empty]

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            "nome_aba": self.name,
            "indicador": self.indicator_name,
            "linha_cabecalho": self.header_row,
            "inicio_dados": self.data_start_row,
            "colunas_por_ano": self.year_columns,
            "total_celulas": len(self.cells),
            "celulas_vazias": len(self.get_empty_cells()),
            "celulas": [c.to_dict() for c in self.cells],
        }


@dataclass
class SpreadsheetMap:
    """
    Mapeamento completo da planilha de entrada.

    Produzido pelo Agente 1 e consumido pelos demais agentes.
    """

    municipality: MunicipalityInfo
    """Informações do município."""

    sheets: List[SheetMapping] = field(default_factory=list)
    """Mapeamento de todas as abas."""

    input_file: str = ""
    """Caminho do arquivo de entrada."""

    total_sheets: int = 0
    """Total de abas encontradas."""

    indicators_found: List[str] = field(default_factory=list)
    """Indicadores já preenchidos."""

    indicators_missing: List[str] = field(default_factory=list)
    """Indicadores faltantes (a serem preenchidos)."""

    def get_all_empty_cells(self) -> List[CellMapping]:
        """Retorna todas as células vazias de todas as abas."""
        cells: List[CellMapping] = []
        for sheet in self.sheets:
            cells.extend(sheet.get_empty_cells())
        return cells

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para JSON estruturado (saída do Agente 1)."""
        return {
            "municipio": self.municipality.nome,
            "estado": self.municipality.estado,
            "codigo_ibge": self.municipality.codigo_ibge,
            "anos": self.municipality.anos,
            "arquivo_entrada": self.input_file,
            "total_abas": self.total_sheets,
            "indicadores_encontrados": self.indicators_found,
            "indicadores_faltantes": self.indicators_missing,
            "abas": [s.to_dict() for s in self.sheets],
            "total_celulas_vazias": len(self.get_all_empty_cells()),
        }
