import streamlit as st


def render_quadro_distribuicao_selector(quantidade_carregadores: int) -> None:
    if quantidade_carregadores > 1:
        st.radio(
            "Quadro de distribuição",
            ["", "Sim", "Não"],
            horizontal=True,
            key="quadro_distribuicao",
        )
    else:
        st.session_state["quadro_distribuicao"] = ""


def render_quadro_distribuicao_distancias() -> float:
    total_quadro = 0.0

    if st.session_state.get("quadro_distribuicao", "") == "Sim":
        with st.expander("📊 Soma da Distância do Quadro de Distribuição com Direções", expanded=False):
            if "percursos_quadro" not in st.session_state:
                st.session_state.percursos_quadro = []

            with st.form(key="percurso_quadro_form"):
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    st.selectbox(
                        "Direção", ["↑", "↓", "→", "←", "↷", "↶"], key="direcao_quadro"
                    )
                with col_b:
                    st.number_input(
                        "Distância (m)", min_value=0.0, step=0.5, key="trecho_quadro"
                    )
                submitted_quadro = st.form_submit_button("Adicionar trecho")

            if submitted_quadro:
                st.session_state.percursos_quadro.append(
                    (st.session_state.direcao_quadro, st.session_state.trecho_quadro)
                )

            if st.session_state.percursos_quadro:
                total_quadro = sum(t[1] for t in st.session_state.percursos_quadro)
                total_quadro_str = f"{total_quadro:g}"
                st.markdown("**Trechos registrados:**")
                for i, (d, t) in enumerate(st.session_state.percursos_quadro):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"{i+1}. {d} {t} m")
                    with col2:
                        if st.button("❌", key=f"delete_quadro_{i}"):
                            st.session_state.percursos_quadro.pop(i)
                            st.rerun()
                st.markdown(f"**Total: {total_quadro_str} m**")

    st.session_state["distancia_alimentacao_distribuicao"] = total_quadro
    return total_quadro
