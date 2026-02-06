import streamlit as st
import pandas as pd
import math
from io import BytesIO


def render_custos_servico_tab(tab_servico, format_currency):
    """Renderiza a aba 'Custo Mão de Obra'."""
    with tab_servico:
        st.subheader("🧰 Custo Mão de Obra")

        st.markdown(
            "<h1 style='font-size:36px;'>🛠️ Instalação</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<h2 style='font-size:30px;'>Técnicos</h2>",
            unsafe_allow_html=True,
        )
        opcoes_instalacao = [
            "Projetista",
            "Eletrotécnico 1",
            "Eletrotécnico 2",
            "Auxiliar Eletricista 1",
            "Auxiliar Eletricista 2",
            "Ajudante",
        ]
        cols = st.columns(len(opcoes_instalacao))
        instalacao_selecionados = []
        for i, (col, opcao) in enumerate(zip(cols, opcoes_instalacao)):
            checkbox_key = f"instalacao_opcao_{i}"
            if checkbox_key not in st.session_state:
                st.session_state[checkbox_key] = opcao == "Eletrotécnico 1"
            with col:
                if st.checkbox(opcao, key=checkbox_key):
                    instalacao_selecionados.append(opcao)
        st.session_state["instalacao_selecionados"] = instalacao_selecionados
        df_profs = st.session_state.get("valores_profissionais_df")
        if df_profs is None:
            try:
                df_profs = pd.read_csv("valores_profissionais.csv", sep=";")
            except FileNotFoundError:
                df_profs = pd.DataFrame(columns=["Profissional", "Valor Hora"])
        if not df_profs.empty:
            df_profs["Valor Hora"] = (
                df_profs["Valor Hora"]
                .astype(str)
                .str.replace(r"R\$\s*", "", regex=True)
                .str.replace(r"\.", "", regex=True)
                .str.replace(",", ".", regex=True)
                .pipe(pd.to_numeric, errors="coerce")
                .fillna(0.0)
            )
        total_tecnicos = 0.0
        total_alimentacao = 0.0
        tecnico_dados = []
        total_refeicoes = 0
        if instalacao_selecionados:
            header_cols = st.columns([3, 2, 2])
            header_cols[0].write("Técnico")
            header_cols[1].write("Horas previstas")
            header_cols[2].write("Total (R$)")

            for idx, tecnico in enumerate(instalacao_selecionados):
                col1, col2, col3 = st.columns([3, 2, 2])
                col1.write(tecnico)
                horas_key = f"horas_{idx}"
                tecnico_associado_key = f"{horas_key}_tecnico"
                if st.session_state.get(tecnico_associado_key) != tecnico:
                    st.session_state[horas_key] = 8.0
                    st.session_state[tecnico_associado_key] = tecnico
                horas = col2.number_input(
                    "Horas",
                    min_value=0.0,
                    step=1.0,
                    value=st.session_state.get(horas_key, 0.0),
                    key=horas_key,
                )
                valor_hora = 0.0
                if not df_profs.empty:
                    match = df_profs.loc[
                        df_profs["Profissional"] == tecnico, "Valor Hora"
                    ]
                    if not match.empty:
                        valor_hora = float(match.iloc[0])
                total = horas * valor_hora
                total_tecnicos += total
                refeicoes = max(1, math.ceil(horas / 8))
                total_alimentacao += refeicoes * 40.0
                total_refeicoes += refeicoes
                tecnico_dados.append(
                    {
                        "Item": tecnico,
                        "Valor Unitário": format_currency(valor_hora),
                        "Quantidade": f"{horas:.2f}",
                        "Total": format_currency(total),
                    }
                )
                total_key = f"total_{idx}"
                st.session_state[total_key] = format_currency(total)
                col3.text_input(
                    "Total",
                    value=st.session_state[total_key],
                    disabled=True,
                    key=total_key,
                )

            st.write(f"Total: {format_currency(total_tecnicos)}")
            st.markdown(
                "<span style='font-size:20px;'>🍽️ <strong>Alimentação</strong></span>",
                unsafe_allow_html=True,
            )
            st.text_input(
                "Alimentação (Total)",
                value=format_currency(total_alimentacao),
                disabled=True,
                key="alimentacao_total",
                label_visibility="collapsed",
            )
            st.session_state["total_tecnicos_servico"] = total_tecnicos
            st.session_state["total_alimentacao_servico"] = total_alimentacao
        else:
            st.info("Nenhum técnico selecionado.")

        servicos_adicionais_campos = [
            ("obra_civil", "Obra Civil"),
            ("infra_rede", "Infra de rede"),
            ("andaime", "Andaime"),
            ("pintura_vaga", "Pintura da vaga"),
            ("pintura_eletrodutos", "Pintura do eletrodutos"),
            ("caminhao_munk", "Caminhão Munk"),
        ]

        servicos_adicionais_selecionados = [
            (chave, nome)
            for chave, nome in servicos_adicionais_campos
            if st.session_state.get(chave) == "Sim"
        ]

        total_servicos_adicionais = 0.0

        if servicos_adicionais_selecionados:
            with st.expander("🔧 Serviços Adicionais", expanded=False):
                for chave, nome in servicos_adicionais_selecionados:
                    campo_custo = f"custo_{chave}"
                    campo_widget = f"custos_servico_{campo_custo}"
                    valor_inicial = float(st.session_state.get(campo_custo, 0.0) or 0.0)

                    if campo_widget not in st.session_state:
                        st.session_state[campo_widget] = valor_inicial

                    custo_servico = st.number_input(
                        f"{nome} (R$)",
                        min_value=0.0,
                        step=0.01,
                        key=campo_widget,
                        value=st.session_state[campo_widget],
                    )
                    st.session_state[campo_custo] = custo_servico
                    total_servicos_adicionais += custo_servico

                st.markdown(
                    f"<p style='color: black; font-size: 18px;'>🛠️ Total Serviços Adicionais: {format_currency(total_servicos_adicionais)}</p>",
                    unsafe_allow_html=True,
                )
        else:
            for chave, _ in servicos_adicionais_campos:
                st.session_state[f"custo_{chave}"] = 0.0

        st.session_state["total_servicos_adicionais"] = total_servicos_adicionais

        total_mao_obra_valor = total_tecnicos + total_alimentacao + total_servicos_adicionais
        st.markdown(
            f"<p style='color: green; font-size: 40px;'>💰 Total Custo Mão de Obra: {format_currency(total_mao_obra_valor)}</p>",
            unsafe_allow_html=True,
        )
        st.session_state["total_custo_mao_obra"] = total_mao_obra_valor
        relatorio_dados = tecnico_dados.copy()
        if total_alimentacao > 0:
            relatorio_dados.append(
                {
                    "Item": "Alimentação",
                    "Valor Unitário": format_currency(40.0),
                    "Quantidade": f"{total_refeicoes}",
                    "Total": format_currency(total_alimentacao),
                }
            )
        if total_servicos_adicionais > 0:
            for chave, nome in servicos_adicionais_selecionados:
                valor_servico = st.session_state.get(f"custo_{chave}", 0.0)
                relatorio_dados.append(
                    {
                        "Item": nome,
                        "Valor Unitário": format_currency(valor_servico),
                        "Quantidade": "1",
                        "Total": format_currency(valor_servico),
                    }
                )
        relatorio_df = pd.DataFrame(relatorio_dados)
        if not relatorio_df.empty:
            buffer = BytesIO()
            try:
                relatorio_df.to_excel(buffer, index=False)
            except ImportError:
                st.error(
                    "Não foi possível gerar o relatório porque a biblioteca "
                    "'openpyxl' não está instalada. Execute `pip install openpyxl` "
                    "e tente novamente."
                )
            else:
                st.download_button(
                    label="Salvar Relatório Custo Mão de Obra",
                    data=buffer.getvalue(),
                    file_name="relatorio_custo_mao_obra.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
