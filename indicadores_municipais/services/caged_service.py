# -*- coding: utf-8 -*-
"""
Serviço de coleta de dados do Novo CAGED.

Coleta admissões, desligamentos, saldo e estoque de empregos formais
via microdados FTP do Ministério do Trabalho ou API SIDRA.
"""

import ftplib
import io
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from config.settings import settings
from config.sources import data_sources
from models.indicators import CAGEDData, YearlyRecord
from services.base_service import BaseService


class CAGEDService(BaseService):
    """
    Serviço para coleta de dados do Novo CAGED.

    Estratégia:
    1. Tenta via API SIDRA (dados agregados, mais rápido)
    2. Fallback: download de microdados FTP (mais granular)
    """

    def __init__(self) -> None:
        super().__init__("CAGEDService")

    def coletar(self, codigo_ibge: str, anos: List[int]) -> CAGEDData:
        """
        Coleta dados do CAGED para o município.

        Args:
            codigo_ibge: Código IBGE de 7 dígitos.
            anos: Anos a coletar.

        Returns:
            Dados CAGED com admissões, desligamentos, saldo e estoque.
        """
        self.logger.info(
            f"Iniciando coleta CAGED para município {codigo_ibge}, anos {anos}"
        )

        # Verificar cache
        cache_key = f"caged_{codigo_ibge}_{'_'.join(map(str, anos))}"
        cached = self._read_cache(cache_key)
        if cached:
            return self._dict_to_caged_data(cached)

        # Tentar via SIDRA primeiro
        try:
            data = self._coletar_via_sidra(codigo_ibge, anos)
            if data and len(data.saldo) > 0:
                self.logger.info("Dados CAGED coletados via SIDRA com sucesso")
                self._write_cache(cache_key, self._caged_data_to_dict(data))
                return data
        except Exception as e:
            self.logger.warning(f"Falha na coleta via SIDRA: {e}")

        # Fallback: microdados FTP
        try:
            data = self._coletar_via_ftp(codigo_ibge, anos)
            if data and len(data.saldo) > 0:
                self.logger.info("Dados CAGED coletados via FTP com sucesso")
                self._write_cache(cache_key, self._caged_data_to_dict(data))
                return data
        except Exception as e:
            self.logger.error(f"Falha na coleta via FTP: {e}")

        self.logger.error("Não foi possível coletar dados do CAGED")
        return CAGEDData()

    def _coletar_via_sidra(
        self, codigo_ibge: str, anos: List[int]
    ) -> CAGEDData:
        """
        Coleta dados do CAGED via API SIDRA.

        Usa a biblioteca sidrapy para consultar tabelas agregadas.

        Args:
            codigo_ibge: Código IBGE do município.
            anos: Anos de interesse.

        Returns:
            Dados CAGED preenchidos.
        """
        try:
            import sidrapy
        except ImportError:
            self.logger.warning("sidrapy não instalado, pulando coleta via SIDRA")
            raise ImportError("sidrapy não disponível")

        data = CAGEDData()

        # A SIDRA pode não ter tabelas específicas do CAGED por município.
        # Tentamos as tabelas disponíveis.
        # Tabela 9906 — CAGED: Saldo de movimentação
        try:
            periodo = ",".join(str(a) for a in anos)

            result = sidrapy.get_table(
                table_code="9906",
                territorial_level="6",
                ibge_territorial_code=codigo_ibge,
                variable="all",
                period=periodo,
            )

            if result is not None and len(result) > 1:
                df = pd.DataFrame(result)
                df = df.iloc[1:]  # Remover linha de cabeçalho

                for _, row in df.iterrows():
                    ano = int(str(row.get("D2C", "0"))[:4])
                    if ano not in anos:
                        continue

                    valor = row.get("V", None)
                    if valor and valor != "...":
                        try:
                            valor_float = float(str(valor).replace(".", "").replace(",", "."))
                        except (ValueError, TypeError):
                            continue

                        variavel = str(row.get("D1C", ""))
                        record = YearlyRecord(
                            ano=ano,
                            valor=valor_float,
                            fonte="SIDRA/CAGED",
                        )

                        # Classificar por tipo de variável
                        if "admiss" in variavel.lower():
                            data.admissoes.append(record)
                        elif "deslig" in variavel.lower():
                            data.desligamentos.append(record)
                        elif "saldo" in variavel.lower():
                            data.saldo.append(record)
                        elif "estoqu" in variavel.lower():
                            data.estoque.append(record)

        except Exception as e:
            self.logger.debug(f"Tabela SIDRA 9906 não disponível: {e}")

        return data

    def _coletar_via_ftp(
        self, codigo_ibge: str, anos: List[int]
    ) -> CAGEDData:
        """
        Coleta dados do CAGED via microdados FTP.

        Baixa arquivos de movimentação mensal do servidor FTP do PDET
        e agrega por ano para o município especificado.

        Args:
            codigo_ibge: Código IBGE do município (usa 6 primeiros dígitos).
            anos: Anos de interesse.

        Returns:
            Dados CAGED agregados por ano.
        """
        data = CAGEDData()
        codigo_6 = codigo_ibge[:6]  # CAGED usa código de 6 dígitos

        for ano in anos:
            self.logger.info(f"Processando CAGED FTP - Ano {ano}")
            try:
                admissoes_ano = 0
                desligamentos_ano = 0
                meses_processados = 0

                # Conectar ao FTP para cada ano
                ftp = ftplib.FTP(
                    data_sources.caged.FTP_HOST,
                    timeout=settings.FTP_TIMEOUT,
                )
                ftp.login()  # Acesso anônimo

                # Listar diretórios do ano
                base_path = f"{data_sources.caged.FTP_BASE_PATH}{ano}/"

                try:
                    dirs = ftp.nlst(base_path)
                except ftplib.error_perm:
                    self.logger.warning(f"Diretório FTP não encontrado para {ano}")
                    ftp.quit()
                    data.saldo.append(YearlyRecord(
                        ano=ano, disponivel=False,
                        observacao=f"Dados não disponíveis no FTP para {ano}",
                        fonte="FTP/CAGED",
                    ))
                    continue

                for dir_path in sorted(dirs):
                    try:
                        files = ftp.nlst(dir_path)
                        # Buscar arquivo de movimentações (CAGEDMOV)
                        mov_files = [
                            f for f in files
                            if "CAGEDMOV" in f.upper() and f.upper().endswith(".TXT")
                        ]

                        if not mov_files:
                            # Tentar arquivos .7z
                            z_files = [
                                f for f in files
                                if "CAGEDMOV" in f.upper() and f.upper().endswith(".7Z")
                            ]
                            if z_files:
                                # Processar arquivo .7z
                                for zf in z_files:
                                    adm, des = self._process_7z_file(
                                        ftp, zf, codigo_6
                                    )
                                    admissoes_ano += adm
                                    desligamentos_ano += des
                                    meses_processados += 1
                            continue

                        for mov_file in mov_files:
                            adm, des = self._process_txt_file(
                                ftp, mov_file, codigo_6
                            )
                            admissoes_ano += adm
                            desligamentos_ano += des
                            meses_processados += 1

                    except ftplib.error_perm as e:
                        self.logger.debug(f"Erro ao listar {dir_path}: {e}")
                        continue

                ftp.quit()

                if meses_processados > 0:
                    saldo_ano = admissoes_ano - desligamentos_ano

                    data.admissoes.append(YearlyRecord(
                        ano=ano, valor=float(admissoes_ano),
                        fonte="FTP/CAGED",
                        observacao=f"{meses_processados} meses processados",
                    ))
                    data.desligamentos.append(YearlyRecord(
                        ano=ano, valor=float(desligamentos_ano),
                        fonte="FTP/CAGED",
                        observacao=f"{meses_processados} meses processados",
                    ))
                    data.saldo.append(YearlyRecord(
                        ano=ano, valor=float(saldo_ano),
                        fonte="FTP/CAGED",
                    ))

                    self.logger.info(
                        f"CAGED {ano}: admissões={admissoes_ano}, "
                        f"desligamentos={desligamentos_ano}, saldo={saldo_ano}"
                    )
                else:
                    data.saldo.append(YearlyRecord(
                        ano=ano, disponivel=False,
                        observacao=f"Nenhum mês processado para {ano}",
                        fonte="FTP/CAGED",
                    ))

            except (ftplib.all_errors, OSError) as e:
                self.logger.error(f"Erro FTP para ano {ano}: {e}")
                data.saldo.append(YearlyRecord(
                    ano=ano, disponivel=False,
                    observacao=f"Erro de conexão FTP: {str(e)[:100]}",
                    fonte="FTP/CAGED",
                ))

        # Calcular estoque acumulado
        self._calcular_estoque(data)

        return data

    def _process_txt_file(
        self, ftp: ftplib.FTP, filepath: str, codigo_municipio: str
    ) -> tuple:
        """
        Processa arquivo .txt de movimentações do CAGED.

        Args:
            ftp: Conexão FTP ativa.
            filepath: Caminho do arquivo no FTP.
            codigo_municipio: Código de 6 dígitos do município.

        Returns:
            Tupla (admissões, desligamentos) para o município.
        """
        buffer = io.BytesIO()

        try:
            ftp.retrbinary(f"RETR {filepath}", buffer.write)
            buffer.seek(0)

            # Ler CSV com separador ; e encoding UTF-8
            df = pd.read_csv(
                buffer,
                sep=";",
                encoding="utf-8",
                dtype=str,
                on_bad_lines="skip",
            )

            # Normalizar nomes das colunas
            df.columns = [c.strip().lower().replace(" ", "") for c in df.columns]

            # Encontrar coluna de município
            mun_col = None
            for col in df.columns:
                if "municipio" in col or "município" in col:
                    mun_col = col
                    break

            if mun_col is None:
                self.logger.debug(f"Coluna município não encontrada em {filepath}")
                return 0, 0

            # Filtrar por município
            df_mun = df[df[mun_col].astype(str).str.startswith(codigo_municipio)]

            if df_mun.empty:
                return 0, 0

            # Encontrar coluna de saldo
            saldo_col = None
            for col in df_mun.columns:
                if "saldomovimentacao" in col or "saldomovimentação" in col:
                    saldo_col = col
                    break

            if saldo_col is None:
                return 0, 0

            # Contar admissões e desligamentos
            saldos = pd.to_numeric(df_mun[saldo_col], errors="coerce")
            admissoes = int((saldos == 1).sum())
            desligamentos = int((saldos == -1).sum())

            return admissoes, desligamentos

        except Exception as e:
            self.logger.debug(f"Erro ao processar {filepath}: {e}")
            return 0, 0

    def _process_7z_file(
        self, ftp: ftplib.FTP, filepath: str, codigo_municipio: str
    ) -> tuple:
        """
        Processa arquivo .7z de movimentações do CAGED.

        Args:
            ftp: Conexão FTP ativa.
            filepath: Caminho do arquivo .7z no FTP.
            codigo_municipio: Código de 6 dígitos do município.

        Returns:
            Tupla (admissões, desligamentos) para o município.
        """
        try:
            import py7zr
        except ImportError:
            self.logger.warning("py7zr não instalado, impossível extrair .7z")
            return 0, 0

        buffer = io.BytesIO()

        try:
            ftp.retrbinary(f"RETR {filepath}", buffer.write)
            buffer.seek(0)

            admissoes = 0
            desligamentos = 0

            # Extrair .7z em diretório temporário
            with py7zr.SevenZipFile(buffer, mode="r") as archive:
                with tempfile.TemporaryDirectory() as temp_dir:
                    archive.extractall(path=temp_dir)

                    for root, dirs, files in os.walk(temp_dir):
                        for name in files:
                            if name.upper().endswith(".TXT"):
                                txt_path = os.path.join(root, name)
                                df = pd.read_csv(
                                    txt_path,
                                    sep=";",
                                    encoding="utf-8",
                                    dtype=str,
                                    on_bad_lines="skip",
                                )

                                df.columns = [c.strip().lower().replace(" ", "") for c in df.columns]

                                mun_col = None
                                for col in df.columns:
                                    if "municipio" in col or "município" in col:
                                        mun_col = col
                                        break

                                if mun_col is None:
                                    continue

                                df_mun = df[df[mun_col].astype(str).str.startswith(codigo_municipio)]
                                if df_mun.empty:
                                    continue

                                saldo_col = None
                                for col in df_mun.columns:
                                    if "saldomovimentacao" in col or "saldomovimentação" in col:
                                        saldo_col = col
                                        break

                                if saldo_col is None:
                                    continue

                                saldos = pd.to_numeric(df_mun[saldo_col], errors="coerce")
                                admissoes += int((saldos == 1).sum())
                                desligamentos += int((saldos == -1).sum())
                                return admissoes, desligamentos

            return admissoes, desligamentos

        except Exception as e:
            self.logger.debug(f"Erro ao processar .7z {filepath}: {e}")
            return 0, 0

    def _calcular_estoque(self, data: CAGEDData) -> None:
        """
        Calcula estoque acumulado a partir dos saldos anuais.

        O estoque é a soma acumulada dos saldos.

        Args:
            data: Dados CAGED com saldos preenchidos (modifica in-place).
        """
        saldos_ordenados = sorted(
            [s for s in data.saldo if s.disponivel and s.valor is not None],
            key=lambda x: x.ano,
        )

        estoque_acumulado = 0.0
        for saldo in saldos_ordenados:
            estoque_acumulado += saldo.valor
            data.estoque.append(YearlyRecord(
                ano=saldo.ano,
                valor=estoque_acumulado,
                fonte=saldo.fonte,
                observacao="Estoque acumulado a partir dos saldos",
            ))

    # === Serialização ===

    @staticmethod
    def _caged_data_to_dict(data: CAGEDData) -> Dict:
        """Converte CAGEDData para dicionário (para cache)."""
        return data.to_dict()

    @staticmethod
    def _dict_to_caged_data(d: Dict) -> CAGEDData:
        """Converte dicionário do cache para CAGEDData."""
        data = CAGEDData()
        for field_name in ["admissoes", "desligamentos", "saldo", "estoque"]:
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
