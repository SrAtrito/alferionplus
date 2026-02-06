import streamlit as st
import pandas as pd
from datetime import datetime


def _parse_currency_column(series: pd.Series) -> pd.Series:
    """Convert a column with Brazilian Real currency strings to float values."""
    return (
        series.astype(str)
        .str.replace(r"R\$\s*", "", regex=True)
        .str.replace(r"\.", "", regex=True)
        .str.replace(",", ".", regex=True)
        .pipe(pd.to_numeric, errors="coerce")
    )


def render_valores_ce_tab(tab_ce_valores, format_currency):
    """Renderiza a aba de valores de CE."""
    with tab_ce_valores:
        st.subheader("Tabela Preços de CE")

        tabela_precos_ce_padrao = pd.DataFrame(
            [
                {
                    "Fabricante": "E-Wolf",
                    "Modelo": "EW1026",
                    "Potência": "7 kW",
                    "Tensão": "220 V",
                    "Carga": "AC",
                    "Conector": "Tipo 2",
                    "Preço": "R$ 4.303,00",
                },
                {
                    "Fabricante": "E-Wolf",
                    "Modelo": "EW1004",
                    "Potência": "7 kW",
                    "Tensão": "220 V",
                    "Carga": "AC",
                    "Conector": "Tipo 2",
                    "Preço": "R$ 5.500,00",
                },
                {
                    "Fabricante": "E-Wolf",
                    "Modelo": "EW1005",
                    "Potência": "7 kW",
                    "Tensão": "220 V",
                    "Carga": "AC",
                    "Conector": "Tipo 2",
                    "Preço": "R$ 6.096,00",
                },
                {
                    "Fabricante": "ABB",
                    "Modelo": "Terra (AC W7-G5-R-0)",
                    "Potência": "7,4 kW",
                    "Tensão": "220 V",
                    "Carga": "AC",
                    "Conector": "Tipo 2",
                    "Preço": "R$ 4.402,00",
                },
                {
                    "Fabricante": "ABB",
                    "Modelo": "Terra (AC W22-G5-R-C-0)",
                    "Potência": "22 kW",
                    "Tensão": "380 V",
                    "Carga": "AC",
                    "Conector": "Tipo 2",
                    "Preço": "R$ 9.143,37",
                },
                {
                    "Fabricante": "NeoCharge",
                    "Modelo": "nc3000s",
                    "Potência": "7,4 kW",
                    "Tensão": "220 V",
                    "Carga": "AC",
                    "Conector": "Tipo 2",
                    "Preço": "R$ 3.998,07",
                },
                {
                    "Fabricante": "NeoCharge",
                    "Modelo": "nc5000",
                    "Potência": "7,4 kW",
                    "Tensão": "380 V",
                    "Carga": "AC",
                    "Conector": "Tipo 2",
                    "Preço": "R$ 3.719,07",
                },
                {
                    "Fabricante": "NeoCharge",
                    "Modelo": "nc4000s",
                    "Potência": "22 kW",
                    "Tensão": "380 V",
                    "Carga": "AC",
                    "Conector": "Tipo 2",
                    "Preço": "R$ 3.998,07",
                },
                {
                    "Fabricante": "NeoCharge",
                    "Modelo": "nc6000",
                    "Potência": "22 kW",
                    "Tensão": "380 V",
                    "Carga": "AC",
                    "Conector": "Tipo 2",
                    "Preço": "R$ 4.463,07",
                },
                {
                    "Fabricante": "NeoCharge",
                    "Modelo": "ndc30",
                    "Potência": "30 kW",
                    "Tensão": "380 V",
                    "Carga": "DC",
                    "Conector": "CCS2",
                    "Preço": "R$ 59.900,00",
                },
                {
                    "Fabricante": "NeoCharge",
                    "Modelo": "ndc60",
                    "Potência": "60 kW",
                    "Tensão": "380 V",
                    "Carga": "DC",
                    "Conector": "CCS2",
                    "Preço": "R$ 119.900,00",
                },
            ]
        )

        try:
            df_precos_ce_raw = pd.read_csv("tabela_precos_ce.csv", sep=";")
        except FileNotFoundError:
            df_precos_ce_raw = tabela_precos_ce_padrao.copy()
            df_precos_ce_raw["Atualizado"] = ""

        if "Atualizado" not in df_precos_ce_raw.columns:
            df_precos_ce_raw["Atualizado"] = ""

        for coluna in ["Fabricante", "Modelo", "Potência", "Tensão", "Carga", "Conector"]:
            if coluna not in df_precos_ce_raw.columns:
                df_precos_ce_raw[coluna] = ""
            df_precos_ce_raw[coluna] = df_precos_ce_raw[coluna].fillna("").astype(str)

        if "Preço" not in df_precos_ce_raw.columns:
            df_precos_ce_raw["Preço"] = ""

        df_precos_ce_numeric = df_precos_ce_raw.copy()
        df_precos_ce_numeric["Preço"] = _parse_currency_column(
            df_precos_ce_numeric["Preço"]
        ).fillna(0.0)

        df_precos_ce_display = df_precos_ce_raw.copy()
        df_precos_ce_display["Preço"] = (
            df_precos_ce_numeric["Preço"].apply(format_currency).astype("string")
        )

        edited_precos_ce = st.data_editor(
            df_precos_ce_display,
            num_rows="dynamic",
            key="tabela_precos_ce_editor",
            column_config={
                "Fabricante": st.column_config.TextColumn("Fabricante"),
                "Modelo": st.column_config.TextColumn("Modelo"),
                "Potência": st.column_config.TextColumn("Potência"),
                "Tensão": st.column_config.TextColumn("Tensão"),
                "Carga": st.column_config.TextColumn("Carga"),
                "Conector": st.column_config.TextColumn("Conector"),
                "Preço": st.column_config.TextColumn("Preço"),
                "Atualizado": st.column_config.Column("Atualizado", disabled=True),
            },
        )
        st.session_state["tabela_precos_ce_df"] = edited_precos_ce

        if st.button("Salvar tabela de preços de CE", key="salvar_tabela_precos_ce"):
            df_to_save = edited_precos_ce.copy()
            df_to_save["Fabricante"] = df_to_save["Fabricante"].fillna("").astype(str)
            df_to_save["Modelo"] = df_to_save["Modelo"].fillna("").astype(str)
            df_to_save["Potência"] = df_to_save["Potência"].fillna("").astype(str)
            df_to_save["Tensão"] = df_to_save["Tensão"].fillna("").astype(str)
            df_to_save["Carga"] = df_to_save["Carga"].fillna("").astype(str)
            df_to_save["Conector"] = df_to_save["Conector"].fillna("").astype(str)

            df_original_numeric = df_precos_ce_numeric.reindex(df_to_save.index)
            df_original_raw = df_precos_ce_raw.reindex(df_to_save.index)

            if "Atualizado" not in df_original_raw:
                df_original_raw["Atualizado"] = ""

            df_to_save["Preço"] = _parse_currency_column(df_to_save["Preço"])

            hoje = datetime.today().strftime("%d/%m/%Y")
            alterado = df_to_save["Preço"] != df_original_numeric["Preço"]
            df_to_save.loc[alterado & df_to_save["Preço"].notna(), "Atualizado"] = hoje
            df_to_save.loc[~alterado | df_to_save["Preço"].isna(), "Atualizado"] = (
                df_original_raw["Atualizado"].fillna("")
            )

            df_to_save["Preço"] = df_to_save["Preço"].fillna(0.0).apply(
                format_currency
            )

            ordered_columns = [
                "Fabricante",
                "Modelo",
                "Potência",
                "Tensão",
                "Carga",
                "Conector",
                "Preço",
                "Atualizado",
            ]
            df_to_save = df_to_save.reindex(columns=ordered_columns, fill_value="")

            df_to_save.to_csv("tabela_precos_ce.csv", sep=";", index=False)
            st.session_state["tabela_precos_ce_df"] = df_to_save
            st.success("Tabela de preços de CE atualizada com sucesso.")

        st.divider()
