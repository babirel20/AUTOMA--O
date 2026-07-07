# -*- coding: utf-8 -*-
"""
Modelos de dados para indicadores coletados.

Define as estruturas que representam os dados brutos coletados
pelo Agente 2 (Coletor de Dados Oficiais) de cada fonte.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class YearlyRecord:
    """Registro genérico de um valor por ano."""

    ano: int
    """Ano do registro."""

    valor: Optional[float] = None
    """Valor numérico."""

    fonte: str = ""
    """Fonte de onde o dado foi coletado."""

    observacao: str = ""
    """Observação sobre o dado (ex: 'dado estimado', 'não disponível')."""

    disponivel: bool = True
    """Se o dado estava disponível na fonte."""

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            "ano": self.ano,
            "valor": self.valor,
            "fonte": self.fonte,
            "observacao": self.observacao,
            "disponivel": self.disponivel,
        }


@dataclass
class CAGEDData:
    """
    Dados coletados do Novo CAGED.

    Contém movimentações de emprego formal por ano.
    """

    admissoes: List[YearlyRecord] = field(default_factory=list)
    """Admissões por ano."""

    desligamentos: List[YearlyRecord] = field(default_factory=list)
    """Desligamentos por ano."""

    saldo: List[YearlyRecord] = field(default_factory=list)
    """Saldo (admissões - desligamentos) por ano."""

    estoque: List[YearlyRecord] = field(default_factory=list)
    """Estoque de empregos formais por ano."""

    def get_by_year(self, field_name: str, ano: int) -> Optional[YearlyRecord]:
        """Busca um registro pelo ano em um campo específico."""
        records = getattr(self, field_name, [])
        for record in records:
            if record.ano == ano:
                return record
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            "fonte": "Novo CAGED / PDET",
            "admissoes": [r.to_dict() for r in self.admissoes],
            "desligamentos": [r.to_dict() for r in self.desligamentos],
            "saldo": [r.to_dict() for r in self.saldo],
            "estoque": [r.to_dict() for r in self.estoque],
        }


@dataclass
class IBGEData:
    """
    Dados coletados do IBGE.

    Contém população estimada e salário médio por ano.
    """

    populacao: List[YearlyRecord] = field(default_factory=list)
    """População estimada por ano."""

    salario_medio: List[YearlyRecord] = field(default_factory=list)
    """Salário médio mensal dos trabalhadores formais por ano."""

    def get_populacao(self, ano: int) -> Optional[float]:
        """Retorna a população de um ano específico."""
        for record in self.populacao:
            if record.ano == ano and record.disponivel:
                return record.valor
        return None

    def get_salario(self, ano: int) -> Optional[float]:
        """Retorna o salário médio de um ano específico."""
        for record in self.salario_medio:
            if record.ano == ano and record.disponivel:
                return record.valor
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            "fonte": "IBGE SIDRA / Cidades",
            "populacao": [r.to_dict() for r in self.populacao],
            "salario_medio": [r.to_dict() for r in self.salario_medio],
        }


@dataclass
class EmpresasData:
    """
    Dados coletados do Mapa de Empresas.

    Contém abertura/extinção de empresas e tempo de abertura por ano.
    """

    empresas_abertas: List[YearlyRecord] = field(default_factory=list)
    """Número de empresas abertas por ano."""

    empresas_extintas: List[YearlyRecord] = field(default_factory=list)
    """Número de empresas extintas (baixadas) por ano."""

    tempo_medio_abertura: List[YearlyRecord] = field(default_factory=list)
    """Tempo médio de abertura em dias por ano."""

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            "fonte": "Mapa de Empresas / Receita Federal",
            "empresas_abertas": [r.to_dict() for r in self.empresas_abertas],
            "empresas_extintas": [r.to_dict() for r in self.empresas_extintas],
            "tempo_medio_abertura": [r.to_dict() for r in self.tempo_medio_abertura],
        }


@dataclass
class EducacaoData:
    """
    Dados coletados do INEP (Censo Escolar) / QEdu.

    Contém informações sobre educação técnica e ensino médio por ano.
    """

    escolas_tecnicas: List[YearlyRecord] = field(default_factory=list)
    """Número de escolas com oferta técnica/profissionalizante por ano."""

    escolas_ensino_medio: List[YearlyRecord] = field(default_factory=list)
    """Número de escolas com ensino médio por ano."""

    matriculas_etp: List[YearlyRecord] = field(default_factory=list)
    """Matrículas em Educação Técnica Profissionalizante por ano."""

    matriculas_ensino_medio: List[YearlyRecord] = field(default_factory=list)
    """Matrículas em Ensino Médio (todas as modalidades) por ano."""

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            "fonte": "INEP Censo Escolar / QEdu",
            "escolas_tecnicas": [r.to_dict() for r in self.escolas_tecnicas],
            "escolas_ensino_medio": [r.to_dict() for r in self.escolas_ensino_medio],
            "matriculas_etp": [r.to_dict() for r in self.matriculas_etp],
            "matriculas_ensino_medio": [r.to_dict() for r in self.matriculas_ensino_medio],
        }


@dataclass
class CollectedData:
    """
    Consolidação de todos os dados coletados.

    Produzido pelo Agente 2 e consumido pelo Agente 3 (Analista).
    """

    municipio: str = ""
    """Nome do município."""

    codigo_ibge: str = ""
    """Código IBGE do município."""

    anos: List[int] = field(default_factory=list)
    """Anos coletados."""

    caged: CAGEDData = field(default_factory=CAGEDData)
    """Dados do CAGED."""

    ibge: IBGEData = field(default_factory=IBGEData)
    """Dados do IBGE."""

    empresas: EmpresasData = field(default_factory=EmpresasData)
    """Dados do Mapa de Empresas."""

    educacao: EducacaoData = field(default_factory=EducacaoData)
    """Dados de Educação (INEP/QEdu)."""

    erros: List[str] = field(default_factory=list)
    """Lista de erros encontrados durante a coleta."""

    avisos: List[str] = field(default_factory=list)
    """Avisos sobre dados parciais ou estimados."""

    def has_complete_data(self) -> bool:
        """Verifica se todos os dados mínimos estão disponíveis."""
        return (
            len(self.caged.saldo) > 0
            and len(self.ibge.populacao) > 0
            and len(self.empresas.empresas_abertas) > 0
            and len(self.educacao.escolas_tecnicas) > 0
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário completo."""
        return {
            "municipio": self.municipio,
            "codigo_ibge": self.codigo_ibge,
            "anos": self.anos,
            "dados": {
                "caged": self.caged.to_dict(),
                "ibge": self.ibge.to_dict(),
                "empresas": self.empresas.to_dict(),
                "educacao": self.educacao.to_dict(),
            },
            "erros": self.erros,
            "avisos": self.avisos,
        }
