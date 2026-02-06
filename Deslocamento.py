import re
import streamlit as st

# Converte '1h20min' em minutos
def tempo_para_minutos(t: str):
    m = re.match(r"(\d+)h(?:(\d+)min)?", t.replace(" ", ""))
    if not m:
        return 0
    h, mn = int(m.group(1)), int(m.group(2) or 0)
    return h * 60 + mn

# Calcula o custo total de deslocamento segundo a lógica da aba Deslocamento do Excel
def calcula_custo_deslocamento(distancia_km: float, tempo: str, custo_pedagios: float, cfg: dict) -> float:
    # 1) Distância total (ida e volta)
    dist_total = distancia_km

    # 2) Custo de combustível
    if cfg["valor_por_km"] > 0:
        custo_km = cfg["valor_por_km"] * dist_total
    else:
        custo_km = (dist_total / cfg["consumo_medio"]) * cfg["valor_combustivel"]

    # 3) Pedágios
    total_pedagios = custo_pedagios

    # 4) Períodos de visita (minutos)
    minutos = tempo_para_minutos(tempo)
    if minutos >= 300:
        periodos = 2
    elif minutos >= 150:
        periodos = 1
    else:
        periodos = 0

    # 5) Refeição e técnico
    total_refeicao = periodos * cfg["valor_refeicao"]
    total_tecnico = periodos * cfg["valor_tecnico"]

    # 6) Mínimo de visita
    minimo_visita = 50 if total_tecnico < cfg["valor_tecnico"] else 0

    # 7) Adicional noturno
    adicional_noturno = cfg["adicional_noturno"] if minutos > 600 else 0

    # 8) Soma de todos os componentes
    custo_base = (
        custo_km
        + total_pedagios
        + total_refeicao
        + total_tecnico
        + minimo_visita
        + adicional_noturno
        + cfg.get("outros_adicionais", 0)
    )

    # 9) Aplica margem
    custo_total = custo_base * (1 + cfg.get("margem_percentual", 0) / 100)
    return custo_total


def render_deslocamento_tab(tab_deslocamento):
    """Renderiza a aba de Configura\u00e7\u00e3o de Deslocamento."""
    with tab_deslocamento:
        st.title("\u2699\ufe0f Configura\u00e7\u00e3o do C\u00e1lculo de Deslocamento")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            valor_combustivel = st.number_input(
                "Valor do Combust\u00edvel (R$/L)",
                min_value=0.0,
                value=st.session_state["desloc_config"].get("valor_combustivel", 7.50),
                step=0.10,
                key="valor_combustivel",
            )
        with col2:
            consumo_medio = st.number_input(
                "(km/L)",
                min_value=0.1,
                value=st.session_state["desloc_config"].get("consumo_medio", 13.0),
                step=0.1,
                key="consumo_medio",
            )
        with col3:
            valor_por_km = st.number_input(
                "KM Direto (opcional)",
                min_value=0.0,
                value=st.session_state["desloc_config"].get("valor_por_km", 0.0),
                step=0.1,
                key="valor_por_km",
            )
        with col4:
            adicional_noturno = st.number_input(
                "Adicional Noturno (R$)",
                min_value=0.0,
                value=st.session_state["desloc_config"].get("adicional_noturno", 350.0),
                step=1.0,
                key="adicional_noturno",
            )
        col5, col6, col7, col8 = st.columns(4)
        with col5:
            outros_adicionais = st.number_input(
                "Outros Adicionais (R$)",
                min_value=0.0,
                value=st.session_state["desloc_config"].get("outros_adicionais", 0.0),
                step=1.0,
                key="outros_adicionais",
            )
        with col6:
            margem_percentual = st.number_input(
                "Margem (%)",
                min_value=0.0,
                value=st.session_state["desloc_config"].get("margem_percentual", 30.0),
                step=1.0,
                key="margem_percentual",
            )
        with col7:
            valor_refeicao = st.number_input(
                "Valor por Refei\u00e7\u00e3o (R$)",
                min_value=0.0,
                value=st.session_state["desloc_config"].get("valor_refeicao", 60.0),
                step=1.0,
                key="valor_refeicao",
            )
        with col8:
            valor_tecnico = st.number_input(
                "T\u00e9cnico por Per\u00edodo (R$)",
                min_value=0.0,
                value=st.session_state["desloc_config"].get("valor_tecnico", 100.0),
                step=1.0,
                key="valor_tecnico",
            )

        st.session_state["desloc_config"] = {
            "valor_combustivel": valor_combustivel,
            "consumo_medio": consumo_medio,
            "valor_por_km": valor_por_km,
            "adicional_noturno": adicional_noturno,
            "outros_adicionais": outros_adicionais,
            "valor_refeicao": valor_refeicao,
            "valor_tecnico": valor_tecnico,
            "margem_percentual": margem_percentual,
        }

        st.markdown("---")
        st.info(
            "Esses valores ser\u00e3o usados automaticamente no c\u00e1lculo do custo de deslocamento na tela principal."
        )
