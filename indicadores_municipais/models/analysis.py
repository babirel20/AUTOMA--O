# -*- coding: utf-8 -*-
"""
Modelos de dados para análises e resultados de indicadores.

Define as estruturas que representam os indicadores calculados
e suas análises interpretativas, produzidos pelo Agente 3 (Analista).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TrendType(Enum):
    """Classificação da tendência de um indicador."""
    CRESCENTE = "crescente"
    DECRESCENTE = "decrescente"
    ESTAVEL = "estável"
    OSCILANTE = "oscilante"


class DiagnosticType(Enum):
    """Classificação do diagnóstico de um indicador."""
    POSITIVO = "positivo"
    NEGATIVO = "negativo"
    NEUTRO = "neutro"
    ATENCAO = "atenção"


@dataclass
class IndicatorResult:
    """Resultado calculado de um indicador para um ano."""

    ano: int
    """Ano do resultado."""

    valor: Optional[float] = None
    """Valor calculado do indicador."""

    variacao_percentual: Optional[float] = None
    """Variação percentual em relação ao ano anterior."""

    valor_formatado: str = ""
    """Valor formatado para exibição (ex: '1.234,56', '15,3%')."""

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            "ano": self.ano,
            "valor": self.valor,
            "variacao_percentual": self.variacao_percentual,
            "valor_formatado": self.valor_formatado,
        }


@dataclass
class IndicatorAnalysis:
    """
    Análise completa de um indicador.

    Contém resultados numéricos e interpretações textuais.
    """

    nome: str
    """Nome do indicador."""

    descricao: str = ""
    """Descrição do indicador."""

    formula: str = ""
    """Fórmula aplicada."""

    resultados: List[IndicatorResult] = field(default_factory=list)
    """Resultados por ano."""

    # === Análises Interpretativas ===
    diagnostico: DiagnosticType = DiagnosticType.NEUTRO
    """Diagnóstico geral: positivo, negativo, neutro ou atenção."""

    tendencia: TrendType = TrendType.ESTAVEL
    """Tendência identificada no período."""

    crescimento_total: Optional[float] = None
    """Crescimento percentual total no período analisado."""

    anos_retratacao: List[int] = field(default_factory=list)
    """Anos em que houve retração/queda."""

    pontos_fortes: List[str] = field(default_factory=list)
    """Pontos fortes identificados."""

    pontos_criticos: List[str] = field(default_factory=list)
    """Pontos críticos e alertas."""

    texto_analise: str = ""
    """Texto interpretativo completo da análise."""

    observacoes: List[str] = field(default_factory=list)
    """Observações técnicas adicionais."""

    # === Comparações (quando aplicável) ===
    comparacao_brasil: Optional[float] = None
    """Comparação com média brasileira (se aplicável)."""

    comparacao_ocde: Optional[float] = None
    """Comparação com média OCDE (se aplicável)."""

    def get_ultimo_valor(self) -> Optional[float]:
        """Retorna o valor mais recente disponível."""
        if self.resultados:
            for resultado in reversed(self.resultados):
                if resultado.valor is not None:
                    return resultado.valor
        return None

    def get_primeiro_valor(self) -> Optional[float]:
        """Retorna o primeiro valor disponível."""
        for resultado in self.resultados:
            if resultado.valor is not None:
                return resultado.valor
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            "indicador": self.nome,
            "descricao": self.descricao,
            "formula": self.formula,
            "resultados": [r.to_dict() for r in self.resultados],
            "diagnostico": self.diagnostico.value,
            "tendencia": self.tendencia.value,
            "crescimento_total": self.crescimento_total,
            "anos_retratacao": self.anos_retratacao,
            "pontos_fortes": self.pontos_fortes,
            "pontos_criticos": self.pontos_criticos,
            "texto_analise": self.texto_analise,
            "observacoes": self.observacoes,
            "comparacao_brasil": self.comparacao_brasil,
            "comparacao_ocde": self.comparacao_ocde,
        }


@dataclass
class FullAnalysis:
    """
    Análise completa de todos os indicadores.

    Produzido pelo Agente 3 e consumido pelo Agente 4 (Escritor).
    """

    municipio: str = ""
    """Nome do município."""

    estado: str = ""
    """Sigla do estado."""

    periodo: str = ""
    """Período analisado (ex: '2020-2025')."""

    # === Os 7 Indicadores ===
    saldo_empregos: IndicatorAnalysis = field(
        default_factory=lambda: IndicatorAnalysis(
            nome="Saldo dos Empregos Formais",
            descricao="Diferença entre admissões e desligamentos formais",
            formula="Admissões - Desligamentos",
        )
    )

    estoque_empregos: IndicatorAnalysis = field(
        default_factory=lambda: IndicatorAnalysis(
            nome="Estoque de Empregos",
            descricao="Total acumulado de empregos formais ativos",
            formula="Somatório acumulado de saldos",
        )
    )

    abertura_liquida_empresas: IndicatorAnalysis = field(
        default_factory=lambda: IndicatorAnalysis(
            nome="Abertura Líquida de Empresas",
            descricao="Diferença entre empresas abertas e extintas",
            formula="Empresas Abertas - Empresas Extintas",
        )
    )

    tempo_medio_abertura: IndicatorAnalysis = field(
        default_factory=lambda: IndicatorAnalysis(
            nome="Tempo Médio de Abertura de Empresas",
            descricao="Tempo médio em dias para abertura de empresa",
            formula="Média do tempo de registro (dias)",
        )
    )

    salario_medio: IndicatorAnalysis = field(
        default_factory=lambda: IndicatorAnalysis(
            nome="Salário Médio Mensal",
            descricao="Salário médio mensal dos trabalhadores formais",
            formula="Média salarial (R$)",
        )
    )

    percentual_escolas_tecnicas: IndicatorAnalysis = field(
        default_factory=lambda: IndicatorAnalysis(
            nome="Percentual de Escolas Técnicas",
            descricao="Proporção de escolas com oferta técnica em relação ao total de ensino médio",
            formula="(Escolas Técnicas ÷ Escolas Ensino Médio) × 100",
        )
    )

    percentual_alunos_etp: IndicatorAnalysis = field(
        default_factory=lambda: IndicatorAnalysis(
            nome="Percentual de Alunos ETP",
            descricao="Proporção de alunos em educação técnica profissional",
            formula="(Matrículas ETP ÷ Matrículas Ensino Médio) × 100",
        )
    )

    # === Resumo Executivo ===
    resumo_executivo: str = ""
    """Texto do resumo executivo consolidado."""

    conclusoes: List[str] = field(default_factory=list)
    """Conclusões gerais da análise."""

    def get_all_indicators(self) -> List[IndicatorAnalysis]:
        """Retorna lista com todos os 7 indicadores."""
        return [
            self.saldo_empregos,
            self.estoque_empregos,
            self.abertura_liquida_empresas,
            self.tempo_medio_abertura,
            self.salario_medio,
            self.percentual_escolas_tecnicas,
            self.percentual_alunos_etp,
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário completo."""
        return {
            "municipio": self.municipio,
            "estado": self.estado,
            "periodo": self.periodo,
            "indicadores": {
                "saldo_empregos": self.saldo_empregos.to_dict(),
                "estoque_empregos": self.estoque_empregos.to_dict(),
                "abertura_liquida_empresas": self.abertura_liquida_empresas.to_dict(),
                "tempo_medio_abertura": self.tempo_medio_abertura.to_dict(),
                "salario_medio": self.salario_medio.to_dict(),
                "percentual_escolas_tecnicas": self.percentual_escolas_tecnicas.to_dict(),
                "percentual_alunos_etp": self.percentual_alunos_etp.to_dict(),
            },
            "resumo_executivo": self.resumo_executivo,
            "conclusoes": self.conclusoes,
        }
