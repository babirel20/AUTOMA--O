# -*- coding: utf-8 -*-
"""Módulo de modelos de dados."""

from models.municipality import MunicipalityInfo, CellMapping, SheetMapping, SpreadsheetMap
from models.indicators import (
    CAGEDData, IBGEData, EmpresasData, EducacaoData, CollectedData, YearlyRecord
)
from models.analysis import (
    IndicatorResult, IndicatorAnalysis, FullAnalysis, TrendType, DiagnosticType
)

__all__ = [
    "MunicipalityInfo", "CellMapping", "SheetMapping", "SpreadsheetMap",
    "CAGEDData", "IBGEData", "EmpresasData", "EducacaoData", "CollectedData", "YearlyRecord",
    "IndicatorResult", "IndicatorAnalysis", "FullAnalysis", "TrendType", "DiagnosticType",
]
