"""Componentes visuais para os gráficos da aba de Cálculo de Serviço."""
from __future__ import annotations

from typing import Iterable, Tuple

import plotly.express as px
import streamlit as st

Numero = float | int


def _filtrar_valores_etiquetas(valores_etiquetas: Iterable[Tuple[str, Numero]]) -> list[Tuple[str, float]]:
    """Remove itens com valores não positivos e garante que os números sejam floats."""

    filtrados: list[Tuple[str, float]] = []
    for etiqueta, valor in valores_etiquetas:
        try:
            valor_float = float(valor)
        except (TypeError, ValueError):
            continue

        if valor_float > 0:
            filtrados.append((etiqueta, valor_float))

    return filtrados


def _renderizar_grafico_pizza(valores_etiquetas: Iterable[Tuple[str, Numero]], titulo: str) -> None:
    """Renderiza um gráfico de pizza com Plotly a partir dos valores fornecidos."""

    dados = _filtrar_valores_etiquetas(valores_etiquetas)

    if not dados:
        st.info("Não há dados suficientes para exibir o gráfico.")
        return

    etiquetas, valores = zip(*dados)
    figura = px.pie(
        values=valores,
        names=etiquetas,
        title=titulo,
        hole=0.0,
        color=etiquetas,
        color_discrete_map={
            "Materiais": "#e74c3c",
            "Mão de Obra": "#800080",
            "Cálculo de Instalação": "#e74c3c",
            "Lucro": "#2ecc71",
            "Projeto": "#1f77b4",
            "Imposto": "#8B4513",
            "Carregadores": "#FFA500",
            "Deslocamento": "#808080",
            "Depreciação": "#F5F5DC",
            "Adicional": "#000000",
        },
    )
    figura.update_traces(textposition="inside", textinfo="percent+label")
    figura.update_layout(margin=dict(t=60, b=0, l=0, r=0))

    st.plotly_chart(figura, use_container_width=True)


def renderizar_grafico_custos_detalhados(*, dados: dict[str, Numero]) -> None:
    """Exibe o gráfico com a participação de cada item do cálculo do serviço."""

    itens = [
        ("Materiais", dados.get("materiais", 0.0)),
        ("Mão de Obra", dados.get("mao_obra", 0.0)),
        ("Deslocamento", dados.get("deslocamento", 0.0)),
        ("Adicional", dados.get("adicional", 0.0)),
        ("Serviços Adicionais", dados.get("servicos_adicionais", 0.0)),
        ("Projeto", dados.get("projeto", 0.0)),
        ("Carregadores", dados.get("carregadores", 0.0)),
        ("Depreciação", dados.get("depreciacao", 0.0)),
        ("Lucro", dados.get("lucro", 0.0)),
        ("Imposto", dados.get("imposto", 0.0)),
    ]

    _renderizar_grafico_pizza(itens, "Distribuição dos Itens do Serviço")


def renderizar_grafico_blocos_resumo(*, dados: dict[str, Numero]) -> None:
    """Exibe o gráfico com os blocos principais e resultados do cálculo do serviço."""

    itens = [
        ("Cálculo de Instalação", dados.get("calculo_instalacao", 0.0)),
        ("Serviços Adicionais", dados.get("servicos_adicionais", 0.0)),
        ("Projeto", dados.get("projeto", 0.0)),
        ("Depreciação", dados.get("depreciacao", 0.0)),
        ("Lucro", dados.get("lucro", 0.0)),
        ("Imposto", dados.get("imposto", 0.0)),
    ]

    _renderizar_grafico_pizza(itens, "Resumo por Bloco")
