# -*- coding: utf-8 -*-
"""
Configuração das fontes de dados oficiais.

Centraliza todas as URLs, endpoints e parâmetros de acesso
às fontes governamentais de dados.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class CAGEDSources:
    """Fontes de dados do Novo CAGED (Ministério do Trabalho)."""

    # FTP com microdados brutos
    FTP_HOST: str = "ftp.mtps.gov.br"
    FTP_BASE_PATH: str = "/pdet/microdados/NOVO CAGED/"
    FTP_MOVIMENTACOES_DIR: str = "Movimentações"
    FTP_EXCLUIDOS_DIR: str = "Movimentações Excluídas"

    # Colunas relevantes nos microdados
    COLUNAS_RELEVANTES: tuple = (
        "competênciamov",
        "município",
        "saldomovimentação",
        "categoria",
        "graudeinstrução",
        "seção",
    )

    # Código de movimentação
    ADMISSAO: int = 1
    DESLIGAMENTO: int = -1


@dataclass(frozen=True)
class IBGESources:
    """Fontes de dados do IBGE."""

    # API de Localidades
    LOCALIDADES_URL: str = "https://servicodados.ibge.gov.br/api/v1/localidades"
    MUNICIPIOS_ENDPOINT: str = "/municipios"
    ESTADOS_ENDPOINT: str = "/estados"

    # API SIDRA (Sistema IBGE de Recuperação Automática)
    SIDRA_URL: str = "https://apisidra.ibge.gov.br/values"

    # Tabela 6579 — Estimativas da População Residente
    TABELA_POPULACAO: str = "6579"
    VARIAVEL_POPULACAO: str = "9324"  # População residente estimada

    # Tabela 5938 — CEMPRE (salário médio)
    TABELA_SALARIO: str = "5938"
    VARIAVEL_SALARIO: str = "513"  # Salário médio mensal

    # Nível territorial: 6 = Município
    NIVEL_MUNICIPAL: str = "6"

    # API IBGE Cidades
    CIDADES_URL: str = "https://servicodados.ibge.gov.br/api/v3/agregados"


@dataclass(frozen=True)
class EmpresasSources:
    """Fontes de dados do Mapa de Empresas."""

    # Portal Mapa de Empresas
    MAPA_URL: str = "https://www.gov.br/empresas-e-negocios/pt-br/mapa-de-empresas"
    PAINEL_URL: str = "https://www.gov.br/empresas-e-negocios/pt-br/mapa-de-empresas/painel-mapa-de-empresas"

    # Dados Abertos — Base de CNPJs da Receita Federal
    DADOS_ABERTOS_URL: str = "https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj"
    RECEITA_FEDERAL_URL: str = "https://dadosabertos.rfb.gov.br/CNPJ/"

    # Campos de interesse nos dados da RF
    CAMPOS_EMPRESA: tuple = (
        "data_inicio_atividade",
        "data_situacao_cadastral",
        "situacao_cadastral",
        "municipio",
    )


@dataclass(frozen=True)
class INEPSources:
    """Fontes de dados do INEP (Censo Escolar)."""

    # Portal de microdados
    MICRODADOS_URL: str = "https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar"

    # Download direto (padrão de URL)
    DOWNLOAD_PATTERN: str = "https://download.inep.gov.br/dados_abertos/microdados_censo_escolar_{ano}.zip"

    # QEdu como fallback
    QEDU_BASE_URL: str = "https://qedu.org.br"
    QEDU_MUNICIPIO_URL: str = "https://qedu.org.br/municipio/{codigo_ibge}"

    # Colunas relevantes — Arquivo de ESCOLAS
    COLUNAS_ESCOLAS: tuple = (
        "CO_MUNICIPIO",
        "NO_ENTIDADE",
        "TP_DEPENDENCIA",
        "TP_SITUACAO_FUNCIONAMENTO",
        "IN_PROFISSIONALIZANTE",
        "IN_MEDIO",
    )

    # Colunas relevantes — Arquivo de MATRÍCULAS
    COLUNAS_MATRICULAS: tuple = (
        "CO_MUNICIPIO",
        "TP_ETAPA_ENSINO",
        "CO_ENTIDADE",
    )

    # Códigos de etapa de ensino (TP_ETAPA_ENSINO)
    # Ensino Médio Regular
    ETAPAS_ENSINO_MEDIO: tuple = (25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38)
    # Educação Profissional Técnica (Integrada + Concomitante + Subsequente)
    ETAPAS_ETP: tuple = (30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 64, 65, 67, 68, 69, 70, 71, 73, 74)


@dataclass(frozen=True)
class DataSources:
    """Agregador de todas as fontes de dados."""

    caged: CAGEDSources = field(default_factory=CAGEDSources)
    ibge: IBGESources = field(default_factory=IBGESources)
    empresas: EmpresasSources = field(default_factory=EmpresasSources)
    inep: INEPSources = field(default_factory=INEPSources)


# Instância global
data_sources = DataSources()
