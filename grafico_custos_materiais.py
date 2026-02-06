"""Componentes de visualização relacionados aos custos com materiais."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st


def render_pizza_custos_materiais(
    df_blocos: pd.DataFrame, format_currency
) -> None:
    """Renderiza o gráfico de pizza da aba "Custos com Materiais".

    Parameters
    ----------
    df_blocos:
        DataFrame contendo as colunas "Bloco" e "Valor".
    format_currency:
        Função utilizada para formatar os valores monetários.
    """

    if df_blocos.empty:
        return

    total_blocos_valor = df_blocos["Valor"].sum()
    if total_blocos_valor <= 0:
        return

    dados_grafico = df_blocos.copy()
    ordem_blocos = {
        "Cabos": 0,
        "Quadro de Proteção": 1,
        "Infra-Seca": 2,
        "Material Adicional": 3,
    }
    dados_grafico["Ordem"] = dados_grafico["Bloco"].map(ordem_blocos)
    dados_grafico["Percentual"] = dados_grafico["Valor"] / total_blocos_valor
    dados_grafico["PercentualLabel"] = dados_grafico["Percentual"].map(
        lambda valor: f"{valor:.1%}"
    )
    dados_grafico["ValorLabel"] = dados_grafico["Valor"].map(format_currency)

    st.markdown("### Distribuição de Custos por Bloco")
    chart = (
        alt.Chart(dados_grafico)
        .mark_arc(innerRadius=60)
        .encode(
            theta=alt.Theta(
                "Valor:Q",
                stack=True,
                sort=alt.Sort(field="Ordem", order="ascending"),
            ),
            color=alt.Color(
                "Bloco:N",
                legend=alt.Legend(title="Blocos de materiais"),
                scale=alt.Scale(
                    domain=[
                        "Cabos",
                        "Quadro de Proteção",
                        "Infra-Seca",
                        "Material Adicional",
                    ],
                    range=["#FF0000", "#0000FF", "#4A4A4A", "#FDBF6F"],
                ),
            ),
            tooltip=[
                alt.Tooltip("Bloco:N", title="Bloco"),
                alt.Tooltip("ValorLabel:N", title="Valor"),
                alt.Tooltip("PercentualLabel:N", title="Percentual"),
            ],
            order=alt.Order("Ordem:Q", sort="ascending"),
        )
        .properties(height=350)
    )

    st.altair_chart(chart, use_container_width=True)
