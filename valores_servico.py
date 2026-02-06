import streamlit as st
import pandas as pd
from datetime import datetime


def render_valores_servico_tab(tab_servico_valores, format_currency):
    """Renderiza a aba de valores de serviço."""
    with tab_servico_valores:
        st.subheader("Tabela de Preços de Serviços")
        try:
            df_servico = pd.read_csv("valores_servico.csv", sep=";")
            df_servico["Preco"] = (
                df_servico["Preco"]
                .astype(str)
                .str.replace(r"R\$\s*", "", regex=True)
                .str.replace(r"\.", "", regex=True)
                .str.replace(",", ".", regex=True)
                .pipe(pd.to_numeric, errors="coerce")
                .fillna(0.0)
            )
        except FileNotFoundError:
            st.info("Nenhum valor de serviço registrado.")
            df_servico = pd.DataFrame(columns=["Servico", "Preco", "Atualizado"])

        df_display = df_servico.copy()

        edited_df = st.data_editor(
            df_display,
            num_rows="dynamic",
            key="valores_servico_editor",
            column_config={
                "Servico": st.column_config.TextColumn("Serviço"),
                "Preco": st.column_config.NumberColumn("Preço", format="R$ %.2f"),
            },
        )
        st.session_state["valores_servico_df"] = edited_df

        if st.button("Salvar valores de serviço"):
            df_to_save = edited_df.copy()
            df_original = df_servico.reindex(df_to_save.index)
            df_to_save["Atualizado"] = df_original.get("Atualizado").fillna("")
            hoje = datetime.today().strftime("%d/%m/%Y")
            df_to_save["Preco"] = (
                df_to_save["Preco"]
                .astype(str)
                .str.replace(r"R\$\s*", "", regex=True)
                .str.replace(r"\.", "", regex=True)
                .str.replace(",", ".", regex=True)
                .pipe(pd.to_numeric, errors="coerce")
            )
            alterado = df_to_save["Preco"] != df_original["Preco"]
            df_to_save.loc[alterado & df_to_save["Preco"].notna(), "Atualizado"] = hoje
            df_to_save["Preco"] = df_to_save["Preco"].fillna(0.0).apply(format_currency)
            df_to_save.to_csv("valores_servico.csv", sep=";", index=False)
            st.success("Valores de serviço atualizados com sucesso.")

        st.subheader("Tabela Trabalho por Hora")
        try:
            df_profissionais_raw = pd.read_csv("valores_profissionais.csv", sep=";")
        except FileNotFoundError:
            df_profissionais_raw = pd.DataFrame(
                {
                    "Profissional": [
                        "Projetista",
                        "Eletrotécnico 1",
                        "Eletrotécnico 2",
                        "Auxiliar Eletricista 1",
                        "Auxiliar Eletricista 2",
                        "Ajudante",
                    ],
                    "Valor Hora": [61.0, 60.0, 60.0, 38.0, 38.0, 25.0],
                    "Atualizado": [""] * 6,
                }
            )

        if "Atualizado" not in df_profissionais_raw.columns:
            df_profissionais_raw["Atualizado"] = ""

        df_profissionais_numeric = df_profissionais_raw.copy()
        df_profissionais_numeric["Valor Hora"] = (
            df_profissionais_numeric["Valor Hora"]
            .astype(str)
            .str.replace(r"R\$\s*", "", regex=True)
            .str.replace(r"\.", "", regex=True)
            .str.replace(",", ".", regex=True)
            .pipe(pd.to_numeric, errors="coerce")
            .fillna(0.0)
        )

        df_prof_display = df_profissionais_numeric.copy()
        df_prof_display["Valor Hora"] = df_prof_display["Valor Hora"].apply(
            format_currency
        )

        edited_prof_df = st.data_editor(
            df_prof_display,
            num_rows="dynamic",
            key="valores_profissionais_editor",
            column_config={
                "Profissional": st.column_config.Column("Profissional", disabled=True),
                "Valor Hora": st.column_config.TextColumn("Valor Hora"),
                "Atualizado": st.column_config.Column("Atualizado", disabled=True),
            },
        )
        st.session_state["valores_profissionais_df"] = edited_prof_df

        if st.button("Salvar tabela trabalho por hora"):
            df_to_save = edited_prof_df.copy()
            df_original = df_profissionais_numeric.reindex(df_to_save.index)
            df_original_raw = df_profissionais_raw.reindex(df_to_save.index)
            if "Atualizado" not in df_original_raw:
                df_original_raw["Atualizado"] = ""
            df_to_save["Atualizado"] = df_original_raw["Atualizado"].fillna("")
            hoje = datetime.today().strftime("%d/%m/%Y")
            df_to_save["Valor Hora"] = (
                df_to_save["Valor Hora"]
                .astype(str)
                .str.replace(r"R\$\s*", "", regex=True)
                .str.replace(r"\.", "", regex=True)
                .str.replace(",", ".", regex=True)
                .pipe(pd.to_numeric, errors="coerce")
            )
            alterado = df_to_save["Valor Hora"] != df_original["Valor Hora"]
            df_to_save.loc[
                alterado & df_to_save["Valor Hora"].notna(), "Atualizado"
            ] = hoje
            df_to_save["Valor Hora"] = (
                df_to_save["Valor Hora"]
                .fillna(0.0)
                .apply(format_currency)
            )
            df_to_save.to_csv("valores_profissionais.csv", sep=";", index=False)
            st.session_state["valores_profissionais_df"] = df_to_save
            st.success("Tabela trabalho por hora atualizada com sucesso.")

