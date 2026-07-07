# -*- coding: utf-8 -*-
"""
Agente 2 - Pesquisador Web / Coletor de Dados

Script principal que orquestra a coleta de dados de 4 fontes oficiais:
- Novo CAGED
- IBGE Cidades / SIDRA
- Mapa de Empresas
- QEdu / INEP

Uso:
    python agente2_collector.py <CODIGO_IBGE>
"""

import argparse
import json
import sys
from pathlib import Path

from config.settings import settings
from models.indicators import CollectedData
from services.caged_service import CAGEDService
from services.empresas_service import EmpresasService
from services.ibge_service import IBGEService
from services.qedu_service import QEduService
from utils.logger import setup_logger, get_logger

logger = get_logger("Agente2")


def coletar_dados_municipio(codigo_ibge: str) -> CollectedData:
    """
    Executa todos os serviços de coleta para um município.

    Args:
        codigo_ibge: Código IBGE (7 dígitos).

    Returns:
        Objeto CollectedData consolidado.
    """
    anos = settings.ANOS_ANALISE

    # Inicializar dados agregados
    dados = CollectedData(
        municipio="Município Desconhecido (TODO: buscar nome pelo IBGE)",
        codigo_ibge=codigo_ibge,
        anos=anos,
    )

    logger.info(f"Iniciando Agente 2 para município: {codigo_ibge}")
    logger.info(f"Período de análise: {anos}")

    # 1. IBGE
    try:
        svc_ibge = IBGEService()
        dados.ibge = svc_ibge.coletar(codigo_ibge, anos)
    except Exception as e:
        erro = f"Falha ao coletar dados do IBGE: {e}"
        logger.error(erro)
        dados.erros.append(erro)

    # 2. CAGED
    try:
        svc_caged = CAGEDService()
        dados.caged = svc_caged.coletar(codigo_ibge, anos)
    except Exception as e:
        erro = f"Falha ao coletar dados do CAGED: {e}"
        logger.error(erro)
        dados.erros.append(erro)

    # 3. Mapa de Empresas
    try:
        svc_empresas = EmpresasService()
        dados.empresas = svc_empresas.coletar(codigo_ibge, anos)
    except Exception as e:
        erro = f"Falha ao coletar dados do Mapa de Empresas: {e}"
        logger.error(erro)
        dados.erros.append(erro)

    # 4. QEdu
    try:
        svc_qedu = QEduService()
        dados.educacao = svc_qedu.coletar(codigo_ibge, anos)
    except Exception as e:
        erro = f"Falha ao coletar dados de Educação (QEdu): {e}"
        logger.error(erro)
        dados.erros.append(erro)

    # Verificar se há dados suficientes
    if not dados.has_complete_data():
        aviso = "Atenção: A coleta não obteve todos os dados mínimos necessários."
        logger.warning(aviso)
        dados.avisos.append(aviso)
        
    return dados


def exportar_excel(dados: CollectedData, output_file: Path) -> None:
    """Exporta os dados consolidados para uma planilha Excel em abas."""
    import pandas as pd
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # 1. Resumo
        resumo_df = pd.DataFrame([{
            "Município": dados.municipio,
            "Código IBGE": dados.codigo_ibge,
            "Período Analisado": f"{min(dados.anos)} a {max(dados.anos)}",
            "Dados Incompletos": not dados.has_complete_data(),
            "Total de Erros": len(dados.erros)
        }])
        resumo_df.to_excel(writer, sheet_name="Resumo", index=False)
        
        # 2. CAGED
        caged_records = []
        for ano in dados.anos:
            adm = dados.caged.get_by_year("admissoes", ano)
            desl = dados.caged.get_by_year("desligamentos", ano)
            sald = dados.caged.get_by_year("saldo", ano)
            estq = dados.caged.get_by_year("estoque", ano)
            
            caged_records.append({
                "Ano": ano,
                "Admissões": adm.valor if adm else None,
                "Desligamentos": desl.valor if desl else None,
                "Saldo": sald.valor if sald else None,
                "Estoque": estq.valor if estq else None,
                "Disponível": sald.disponivel if sald else False
            })
        pd.DataFrame(caged_records).to_excel(writer, sheet_name="CAGED", index=False)

        # 3. IBGE
        ibge_records = []
        for ano in dados.anos:
            pop = dados.ibge.get_populacao(ano)
            sal = dados.ibge.get_salario(ano)
            ibge_records.append({
                "Ano": ano,
                "População": pop,
                "Salário Médio (R$)": sal,
            })
        pd.DataFrame(ibge_records).to_excel(writer, sheet_name="IBGE", index=False)

        # 4. Mapa de Empresas
        empresas_records = []
        for ano in dados.anos:
            abertas = next((r for r in dados.empresas.empresas_abertas if r.ano == ano), None)
            extintas = next((r for r in dados.empresas.empresas_extintas if r.ano == ano), None)
            tempo = next((r for r in dados.empresas.tempo_medio_abertura if r.ano == ano), None)
            empresas_records.append({
                "Ano": ano,
                "Abertas": abertas.valor if abertas else None,
                "Extintas": extintas.valor if extintas else None,
                "Tempo Médio (dias)": tempo.valor if tempo else None,
            })
        pd.DataFrame(empresas_records).to_excel(writer, sheet_name="Empresas", index=False)

        # 5. QEdu
        qedu_records = []
        for ano in dados.anos:
            tec = next((r for r in dados.educacao.escolas_tecnicas if r.ano == ano), None)
            med = next((r for r in dados.educacao.escolas_ensino_medio if r.ano == ano), None)
            mat_tec = next((r for r in dados.educacao.matriculas_etp if r.ano == ano), None)
            mat_med = next((r for r in dados.educacao.matriculas_ensino_medio if r.ano == ano), None)
            qedu_records.append({
                "Ano": ano,
                "Escolas Técnicas": tec.valor if tec else None,
                "Escolas Ensino Médio": med.valor if med else None,
                "Matrículas ETP": mat_tec.valor if mat_tec else None,
                "Matrículas Ensino Médio": mat_med.valor if mat_med else None,
            })
        pd.DataFrame(qedu_records).to_excel(writer, sheet_name="QEdu", index=False)


def main():
    setup_logger("indicadores_municipais")
    parser = argparse.ArgumentParser(description="Coletor de Dados Municipais (Agente 2)")
    parser.add_argument("codigo_ibge", type=str, help="Código IBGE do município (7 dígitos)")
    
    args = parser.parse_args()
    codigo_ibge = args.codigo_ibge

    if len(codigo_ibge) != 7 or not codigo_ibge.isdigit():
        logger.error("O código IBGE deve conter exatamente 7 dígitos numéricos.")
        sys.exit(1)

    # Executar coleta
    dados = coletar_dados_municipio(codigo_ibge)
    
    # Exportar JSON
    output_dir = settings.OUTPUT_DIR
    output_file_json = output_dir / f"coleta_{codigo_ibge}.json"
    output_file_excel = output_dir / f"coleta_{codigo_ibge}.xlsx"
    
    try:
        with open(output_file_json, "w", encoding="utf-8") as f:
            json.dump(dados.to_dict(), f, ensure_ascii=False, indent=4)
        logger.info(f"✅ Coleta concluída! JSON salvo em: {output_file_json}")
    except IOError as e:
        logger.error(f"Erro ao salvar arquivo JSON: {e}")
        
    try:
        exportar_excel(dados, output_file_excel)
        logger.info(f"✅ Planilha concluída! Excel salvo em: {output_file_excel}")
    except Exception as e:
        logger.error(f"Erro ao salvar planilha Excel: {e}")


if __name__ == "__main__":
    main()
