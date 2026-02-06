import streamlit as st
import pandas as pd

from Deslocamento import calcula_custo_deslocamento, render_deslocamento_tab
from valores_material import render_valores_material_tab
from valores_servico import render_valores_servico_tab
from valores_ce import render_valores_ce_tab
from custos_materiais import render_custos_materiais_tab
from custos_servico import render_custos_servico_tab

def format_currency(value: float) -> str:

    """Format number as Brazilian Real currency."""
    return (
        f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )


def render_custos_tab(tab_custos):
    """Renderiza a aba de custos."""
    with tab_custos:
        st.title("💰 Custos")
        tab_resumo, tab_servico, tab_desloc, tab_atualizacoes = st.tabs(
            [
                "Custos com Materiais",
                "Custo Mão de Obra",
                "Deslocamento",
                "Atualizações",
            ]
        )

        render_custos_materiais_tab(tab_resumo, format_currency)
        render_custos_servico_tab(tab_servico, format_currency)

        with tab_desloc:
            if st.session_state.get("deslocamento_necessario") == "Sim":
                custo_total = calcula_custo_deslocamento(
                    st.session_state.get("distancia_km", 0.0),
                    st.session_state.get("tempo_viagem", ""),
                    st.session_state.get("custo_pedagios", 0.0),
                    st.session_state["desloc_config"],
                )
                st.session_state["total_custo_deslocamento"] = custo_total
                st.success(
                    f"💰 Custo estimado de deslocamento: R$ {custo_total:,.2f}"
                )
            else:
                st.session_state["total_custo_deslocamento"] = 0.0
                st.info("Nenhum custo de deslocamento calculado.")

        with tab_atualizacoes:
            (
                tab_material,
                tab_valores_servico,
                tab_valores_ce,
                tab_config_desloc,
            ) = st.tabs([
                "Valores de Material",
                "Valores de Serviço",
                "Valores de CE",
                "Configuração de Deslocamento",
            ])
            render_valores_material_tab(tab_material, format_currency)
            render_valores_servico_tab(tab_valores_servico, format_currency)
            render_valores_ce_tab(tab_valores_ce, format_currency)
            render_deslocamento_tab(tab_config_desloc)

