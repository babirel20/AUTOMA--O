# -*- coding: utf-8 -*-
"""
Formatadores de saída.

Funções para formatar números, percentuais, moedas e textos
para exibição na planilha e nas análises.
"""

import locale
from typing import Optional

from config.settings import settings


class Formatter:
    """Formatador de valores para exibição."""

    @staticmethod
    def numero(valor: Optional[float], casas: int = 0) -> str:
        """
        Formata número com separadores de milhar brasileiro.

        Args:
            valor: Valor numérico.
            casas: Casas decimais.

        Returns:
            Número formatado (ex: '1.234.567' ou '1.234,56').
        """
        if valor is None:
            return "N/D"

        if casas == 0:
            formatted = f"{valor:,.0f}"
        else:
            formatted = f"{valor:,.{casas}f}"

        # Converter formato americano para brasileiro
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return formatted

    @staticmethod
    def percentual(valor: Optional[float], casas: int = 1) -> str:
        """
        Formata valor como percentual.

        Args:
            valor: Valor percentual (ex: 15.3 para 15,3%).
            casas: Casas decimais.

        Returns:
            Percentual formatado (ex: '15,3%').
        """
        if valor is None:
            return "N/D"

        formatted = f"{valor:,.{casas}f}"
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{formatted}%"

    @staticmethod
    def variacao(valor: Optional[float], casas: int = 1) -> str:
        """
        Formata variação percentual com sinal.

        Args:
            valor: Variação percentual.
            casas: Casas decimais.

        Returns:
            Variação formatada (ex: '+5,3%', '-2,1%').
        """
        if valor is None:
            return "N/D"

        sinal = "+" if valor > 0 else ""
        formatted = f"{valor:,.{casas}f}"
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{sinal}{formatted}%"

    @staticmethod
    def moeda(valor: Optional[float], casas: int = 2) -> str:
        """
        Formata valor como moeda brasileira.

        Args:
            valor: Valor monetário.
            casas: Casas decimais.

        Returns:
            Valor em Real (ex: 'R$ 2.345,67').
        """
        if valor is None:
            return "N/D"

        formatted = f"{valor:,.{casas}f}"
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{settings.CURRENCY_SYMBOL} {formatted}"

    @staticmethod
    def dias(valor: Optional[float]) -> str:
        """
        Formata valor como tempo em dias.

        Args:
            valor: Número de dias.

        Returns:
            Tempo formatado (ex: '2 dias e 5 horas').
        """
        if valor is None:
            return "N/D"

        dias_inteiros = int(valor)
        horas = int((valor - dias_inteiros) * 24)

        if horas > 0:
            return f"{dias_inteiros} dia(s) e {horas}h"
        return f"{dias_inteiros} dia(s)"

    @staticmethod
    def tendencia_emoji(tendencia: str) -> str:
        """
        Retorna emoji indicando a tendência.

        Args:
            tendencia: Tipo de tendência.

        Returns:
            Emoji correspondente.
        """
        mapa = {
            "crescente": "📈",
            "decrescente": "📉",
            "estável": "➡️",
            "oscilante": "📊",
        }
        return mapa.get(tendencia, "❓")

    @staticmethod
    def diagnostico_texto(diagnostico: str) -> str:
        """
        Retorna texto descritivo do diagnóstico.

        Args:
            diagnostico: Tipo de diagnóstico.

        Returns:
            Texto descritivo.
        """
        mapa = {
            "positivo": "Situação favorável",
            "negativo": "Situação desfavorável",
            "neutro": "Situação neutra/estável",
            "atenção": "Requer atenção",
        }
        return mapa.get(diagnostico, "Não avaliado")
