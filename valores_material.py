import streamlit as st
import pandas as pd
from datetime import datetime

from dados_transformadores import obter_transformadores_padrao


def render_valores_material_tab(tab_material, format_currency):
    """Renderiza a aba de valores de material."""
    with tab_material:
        with st.expander("🔌 Tabela de Preços Cabos", expanded=True):
            try:
                df_cabos_raw = pd.read_csv("valores_cabos.csv", sep=";")
                for col in ["Preco 750V", "Preco 1kV"]:
                    df_cabos_raw[col] = (
                        df_cabos_raw[col]
                        .astype(str)
                        .str.replace(r"R\$\s*", "", regex=True)
                        .str.replace(r"\.", "", regex=True)
                        .str.replace(",", ".", regex=True)
                        .pipe(pd.to_numeric, errors="coerce")
                        .fillna(0.0)
                    )
            except FileNotFoundError:
                st.info("Nenhum valor de material registrado.")
                df_cabos_raw = pd.DataFrame(
                    columns=[
                        "Cabo 750V",
                        "Preco 750V",
                        "Atualizado 750V",
                        "Cabo 1kV",
                        "Preco 1kV",
                        "Atualizado 1kV",
                    ]
                )

            df_cabos_display = df_cabos_raw.copy()
            for col in ["Preco 750V", "Preco 1kV"]:
                df_cabos_display[col] = df_cabos_display[col].apply(format_currency)

            edited_df = st.data_editor(
                df_cabos_display,
                num_rows="dynamic",
                key="valores_cabos_editor",
                column_config={
                    "Preco 750V": st.column_config.TextColumn("Preco 750V"),
                    "Preco 1kV": st.column_config.TextColumn("Preco 1kV"),
                },
            )
            st.session_state["valores_cabos_df"] = edited_df
            if st.button("Salvar valores de cabos"):
                df_to_save = edited_df.copy()
                df_original = df_cabos_raw.reindex(df_to_save.index)
                df_to_save["Atualizado 750V"] = df_original.get("Atualizado 750V").fillna("")
                df_to_save["Atualizado 1kV"] = df_original.get("Atualizado 1kV").fillna("")
                hoje = datetime.today().strftime("%d/%m/%Y")
                for col in ["Preco 750V", "Preco 1kV"]:
                    df_to_save[col] = (
                        df_to_save[col]
                        .astype(str)
                        .str.replace(r"R\$\s*", "", regex=True)
                        .str.replace(r"\.", "", regex=True)
                        .str.replace(",", ".", regex=True)
                        .pipe(pd.to_numeric, errors="coerce")
                    )
                alterado_750 = df_to_save["Preco 750V"] != df_original["Preco 750V"]
                alterado_1kv = df_to_save["Preco 1kV"] != df_original["Preco 1kV"]
                df_to_save.loc[
                    alterado_750 & df_to_save["Preco 750V"].notna(), "Atualizado 750V"
                ] = hoje
                df_to_save.loc[
                    alterado_1kv & df_to_save["Preco 1kV"].notna(), "Atualizado 1kV"
                ] = hoje
                for col in ["Preco 750V", "Preco 1kV"]:
                    df_to_save[col] = df_to_save[col].fillna(0.0).apply(format_currency)
                df_to_save.to_csv("valores_cabos.csv", sep=";", index=False)
                st.success("Valores de cabos atualizados com sucesso.")

        with st.expander("🧰 Tabelas de Infra-Seca", expanded=False):
            try:
                df_eletrodutos_raw = pd.read_csv("valores_eletrodutos.csv", sep=";")
                df_eletrodutos_raw["Material"] = (
                    df_eletrodutos_raw["Material"]
                    .astype(str)
                    .str.replace("\u201d", "", regex=False)
                    .str.replace('"', "", regex=False)
                    .str.strip()
                )
                df_eletrodutos_raw["Preco"] = (
                    df_eletrodutos_raw["Preco"]
                    .astype(str)
                    .str.replace(r"R\$\s*", "", regex=True)
                    .str.replace(r"\.", "", regex=True)
                    .str.replace(",", ".", regex=True)
                    .pipe(pd.to_numeric, errors="coerce")
                    .fillna(0.0)
                )

                def editar_tabela(df_raw, mask, titulo, key_prefix, botao, sealtubo=False):
                    with st.expander(titulo, expanded=False):
                        df_subset = df_raw[mask].copy()
                        if df_subset.empty:
                            st.info(f"Nenhum valor de {titulo.lower()} registrado.")
                            return df_raw
                        df_display = df_subset.copy().drop(
                            columns=["Categoria"], errors="ignore"
                        )
                        df_display["Preco"] = df_display["Preco"].apply(format_currency)
                        column_config = {
                            "Material": st.column_config.Column(
                                "Sealtubo" if sealtubo else "Material", disabled=True
                            ),
                            "Preco": st.column_config.TextColumn("Preço"),
                            "Atualizado": st.column_config.Column(
                                "Atualizado", disabled=True
                            ),
                        }
                        edited = st.data_editor(
                            df_display,
                            num_rows="dynamic",
                            key=f"{key_prefix}_editor",
                            column_config=column_config,
                        )
                        if st.button(botao, key=f"{key_prefix}_save"):
                            df_to_save = edited.copy()
                            df_original = df_subset.reindex(df_to_save.index)
                            df_to_save["Atualizado"] = (
                                df_original.get("Atualizado").fillna("")
                            )
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
                            df_to_save.loc[
                                alterado & df_to_save["Preco"].notna(), "Atualizado"
                            ] = hoje
                            df_raw.update(df_to_save)
                            if sealtubo:
                                st.session_state["valores_sealtubo_df"] = df_to_save[
                                    ["Material", "Preco"]
                                ].rename(columns={"Material": "Sealtubo"})
                            df_to_csv = df_raw.copy()
                            df_to_csv["Preco"] = df_to_csv["Preco"].fillna(0.0).apply(
                                format_currency
                            )
                            df_to_csv.to_csv("valores_eletrodutos.csv", sep=";", index=False)
                            st.session_state["valores_eletrodutos_df"] = df_to_csv
                            st.success(
                                f"{botao.replace('Salvar ', '')} atualizados com sucesso."
                            )
                    return df_raw

                def editar_conduletes(
                    df_raw, mask, titulo, key_prefix, botao, tipo_rotulo
                ):
                    with st.expander(titulo, expanded=False):
                        df_subset = df_raw[mask].copy()
                        if df_subset.empty:
                            st.info(f"Nenhum valor de {titulo.lower()} registrado.")
                            return df_raw
                        df_subset["Tamanho"] = df_subset["Material"].str.extract(
                            r"Condulete s/rosca ([\d\s/]+)", expand=False
                        ).str.strip()
                        df_grouped = (
                            df_subset.groupby("Tamanho")["Preco"].first().reset_index()
                        )
                        ordem = {"3/4": 0, "1": 1, "1 1/4": 2, "1 1/2": 3, "2": 4}
                        df_grouped["ordem"] = df_grouped["Tamanho"].map(ordem)
                        df_grouped = df_grouped.sort_values("ordem").drop(columns="ordem")
                        df_grouped["Condulete"] = df_grouped["Tamanho"].apply(tipo_rotulo)
                        df_display = df_grouped[["Condulete", "Preco"]].copy()
                        df_display["Preco"] = df_display["Preco"].apply(format_currency)
                        edited = st.data_editor(
                            df_display,
                            num_rows="dynamic",
                            key=f"{key_prefix}_editor",
                            column_config={
                                "Condulete": st.column_config.Column(
                                    "Condulete", disabled=True
                                ),
                                "Preco": st.column_config.TextColumn("Preço"),
                            },
                        )
                        if st.button(botao, key=f"{key_prefix}_save"):
                            df_to_save = edited.copy()
                            df_to_save["Preco"] = (
                                df_to_save["Preco"]
                                .astype(str)
                                .str.replace(r"R\$\s*", "", regex=True)
                                .str.replace(r"\.", "", regex=True)
                                .str.replace(",", ".", regex=True)
                                .pipe(pd.to_numeric, errors="coerce")
                            )
                            df_merged = df_grouped.merge(
                                df_to_save, on="Condulete", suffixes=("_orig", "")
                            )
                            hoje = datetime.today().strftime("%d/%m/%Y")
                            for _, row in df_merged.iterrows():
                                tamanho = row["Tamanho"]
                                preco_novo = row["Preco"]
                                preco_orig = row["Preco_orig"]
                                mask_tam = mask & df_subset["Tamanho"].eq(tamanho)
                                if pd.notna(preco_novo):
                                    if preco_novo != preco_orig:
                                        df_raw.loc[
                                            df_subset[mask_tam].index, "Atualizado"
                                        ] = hoje
                                    df_raw.loc[
                                        df_subset[mask_tam].index, "Preco"
                                    ] = preco_novo
                            df_to_csv = df_raw.copy()
                            df_to_csv["Preco"] = df_to_csv["Preco"].fillna(0.0).apply(
                                format_currency
                            )
                            df_to_csv.to_csv("valores_eletrodutos.csv", sep=";", index=False)
                            st.session_state["valores_eletrodutos_df"] = df_to_csv
                            st.success(
                                f"{botao.replace('Salvar ', '')} atualizados com sucesso."
                            )
                    return df_raw

                df_eletrodutos_raw = editar_tabela(
                    df_eletrodutos_raw,
                    df_eletrodutos_raw["Material"].str.contains(
                        "Eletroduto Galv Pre-Zinc", case=False
                    ),
                    "Tabela de Preços Eletrodutos",
                    "eletroduto",
                    "Salvar valores de eletrodutos",
                )
                df_eletrodutos_raw = editar_conduletes(
                    df_eletrodutos_raw,
                    df_eletrodutos_raw["Material"].str.contains(
                        "Condulete s/rosca", case=False
                    )
                    & df_eletrodutos_raw["Material"].str.contains(
                        r"(?:C|LL|LR|X)$", case=False, regex=True
                    ),
                    "Tabela de Preços Conduletes sem rosca C-LL-LR-X",
                    "condulete_cllx",
                    "Salvar valores de conduletes C-LL-LR-X",
                    lambda x: f"Condulete s/rosca {x} C/LL/LR/X",
                )
                df_eletrodutos_raw = editar_conduletes(
                    df_eletrodutos_raw,
                    df_eletrodutos_raw["Material"].str.contains(
                        "Condulete s/rosca", case=False
                    )
                    & df_eletrodutos_raw["Material"].str.contains(
                        r"T$", case=False, regex=True
                    ),
                    "Tabela de Preços Conduletes sem rosca T",
                    "condulete_t",
                    "Salvar valores de conduletes T",
                    lambda x: f"Condulete s/rosca {x} T",
                )
                df_eletrodutos_raw = editar_tabela(
                    df_eletrodutos_raw,
                    df_eletrodutos_raw["Material"].str.contains(
                        "Unidut Reto comum", case=False
                    ),
                    "Tabela de Preços Unidut Reto comum",
                    "unidut_reto",
                    "Salvar valores de unidut reto",
                )
                df_eletrodutos_raw = editar_tabela(
                    df_eletrodutos_raw,
                    df_eletrodutos_raw["Material"].str.contains(
                        "Unidut Conico comum", case=False
                    ),
                    "Tabela de Preços Unidut Cônico Comum",
                    "unidut_conico",
                    "Salvar valores de unidut cônico",
                )
                df_eletrodutos_raw = editar_tabela(
                    df_eletrodutos_raw,
                    df_eletrodutos_raw["Material"].str.contains(
                        "Unilet comum 90º", case=False
                    ),
                    "Tabela de Preços Unilet comum 90º",
                    "unilet",
                    "Salvar valores de unilet",
                )
                df_eletrodutos_raw = editar_tabela(
                    df_eletrodutos_raw,
                    df_eletrodutos_raw["Material"].str.contains(
                        "Curva Galv Eletro", case=False
                    ),
                    "Tabela de Preços Curva Galv Eletro 90º",
                    "curva",
                    "Salvar valores de curva",
                )
                df_eletrodutos_raw = editar_tabela(
                    df_eletrodutos_raw,
                    df_eletrodutos_raw["Material"].str.contains(
                        "Abraçadeira D e cunha", case=False
                    ),
                    "Tabela de Preços Abraçadeira D e Cunha",
                    "abracadeira",
                    "Salvar valores de abraçadeiras",
                )
                editar_tabela(
                    df_eletrodutos_raw,
                    df_eletrodutos_raw["Material"].str.contains(
                        "Flexivel Sealtubo c/capa", case=False
                    ),
                    "Tabela de Preços Sealtubo Com Capa",
                    "sealtubo",
                    "Salvar valores de sealtubo",
                    sealtubo=True,
                )
            except FileNotFoundError:
                st.info("Nenhum valor de eletroduto registrado.")

        with st.expander("🧰 Tabelas de Material para Quadro Elétrico", expanded=False):

            with st.expander("⚡ Tabela de Preços Disjuntores DIN", expanded=False):
                try:
                    df_disjuntores_din_raw = pd.read_csv(
                        "valores_disjuntor_din.csv", sep=";"
                    )
                    df_disjuntores_din_raw["Preco"] = (
                        df_disjuntores_din_raw["Preco"]
                        .astype(str)
                        .str.replace(r"R\$\s*", "", regex=True)
                        .str.replace(r"\.", "", regex=True)
                        .str.replace(",", ".", regex=True)
                        .pipe(pd.to_numeric, errors="coerce")
                        .fillna(0.0)
                    )
                except FileNotFoundError:
                    df_disjuntores_din_raw = pd.DataFrame(
                        columns=["Material", "Preco", "Atualizado"]
                    )

                df_disjuntores_din_display = df_disjuntores_din_raw.copy()
                df_disjuntores_din_display["Preco"] = (
                    df_disjuntores_din_display["Preco"].apply(format_currency)
                )

                edited_disjuntores_din = st.data_editor(
                    df_disjuntores_din_display,
                    num_rows="dynamic",
                    key="valores_disjuntores_din_editor",
                    column_config={
                        "Material": st.column_config.TextColumn("Material"),
                        "Preco": st.column_config.TextColumn("Preço"),
                        "Atualizado": st.column_config.Column("Atualizado", disabled=True),
                    },
                )
                st.session_state["valores_disjuntores_din_df"] = edited_disjuntores_din

                if st.button("Salvar valores de disjuntores DIN"):
                    df_to_save = edited_disjuntores_din.copy()
                    df_original = df_disjuntores_din_raw.reindex(df_to_save.index)
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
                    df_to_save.loc[
                        alterado & df_to_save["Preco"].notna(), "Atualizado"
                    ] = hoje
                    df_to_save["Preco"] = df_to_save["Preco"].fillna(0.0).apply(
                        format_currency
                    )
                    df_to_save.to_csv("valores_disjuntor_din.csv", sep=";", index=False)
                    st.success("Valores de disjuntores DIN atualizados com sucesso.")

            with st.expander("🛡️ Tabela de Preços IDR", expanded=False):
                try:
                    df_idr_raw = pd.read_csv("valores_idr.csv", sep=";")
                    df_idr_raw["Preco"] = (
                        df_idr_raw["Preco"]
                        .astype(str)
                        .str.replace(r"R\$\s*", "", regex=True)
                        .str.replace(r"\.", "", regex=True)
                        .str.replace(",", ".", regex=True)
                        .pipe(pd.to_numeric, errors="coerce")
                        .fillna(0.0)
                    )
                except FileNotFoundError:
                    df_idr_raw = pd.DataFrame(
                        [
                            ["Interruptor DR Tipo A  2P 40A 30mA", 280.00, ""],
                            ["Interruptor DR Tipo A  2P 63A 30mA", 299.00, ""],
                            ["Interruptor DR Tipo A  4P 40A 30mA", 298.00, ""],
                            ["Interruptor DR Tipo A  4P 63A 30mA", 299.00, ""],
                        ],
                        columns=["Material", "Preco", "Atualizado"],
                    )

                df_idr_display = df_idr_raw.copy()
                df_idr_display["Preco"] = df_idr_display["Preco"].apply(format_currency)

                edited_idr = st.data_editor(
                    df_idr_display,
                    num_rows="dynamic",
                    key="valores_idr_editor",
                    column_config={
                        "Material": st.column_config.TextColumn("Material"),
                        "Preco": st.column_config.TextColumn("Preço"),
                        "Atualizado": st.column_config.Column("Atualizado", disabled=True),
                    },
                )
                st.session_state["valores_idr_df"] = edited_idr

                if st.button("Salvar valores de IDR"):
                    df_to_save = edited_idr.copy()
                    df_original = df_idr_raw.reindex(df_to_save.index)
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
                    df_to_save.loc[
                        alterado & df_to_save["Preco"].notna(), "Atualizado"
                    ] = hoje
                    df_to_save["Preco"] = df_to_save["Preco"].fillna(0.0).apply(
                        format_currency
                    )
                    df_to_save.to_csv("valores_idr.csv", sep=";", index=False)
                    st.success("Valores de IDR atualizados com sucesso.")

            with st.expander("⚡ Tabela de Preços DPS", expanded=False):
                try:
                    df_dps_raw = pd.read_csv("valores_dps.csv", sep=";")
                    df_dps_raw["Preco"] = (
                        df_dps_raw["Preco"]
                        .astype(str)
                        .str.replace(r"R\$\s*", "", regex=True)
                        .str.replace(r"\.", "", regex=True)
                        .str.replace(",", ".", regex=True)
                        .pipe(pd.to_numeric, errors="coerce")
                        .fillna(0.0)
                    )
                except FileNotFoundError:
                    df_dps_raw = pd.DataFrame(
                        [["DPS 20kA tipo 2", 40.00, ""]],
                        columns=["Material", "Preco", "Atualizado"],
                    )

                df_dps_display = df_dps_raw.copy()
                df_dps_display["Preco"] = df_dps_display["Preco"].apply(format_currency)

                edited_dps = st.data_editor(
                    df_dps_display,
                    num_rows="dynamic",
                    key="valores_dps_editor",
                    column_config={
                        "Material": st.column_config.TextColumn("Material"),
                        "Preco": st.column_config.TextColumn("Preço"),
                        "Atualizado": st.column_config.Column("Atualizado", disabled=True),
                    },
                )
                st.session_state["valores_dps_df"] = edited_dps

                if st.button("Salvar valores de DPS"):
                    df_to_save = edited_dps.copy()
                    df_original = df_dps_raw.reindex(df_to_save.index)
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
                    df_to_save.loc[
                        alterado & df_to_save["Preco"].notna(), "Atualizado"
                    ] = hoje
                    df_to_save["Preco"] = df_to_save["Preco"].fillna(0.0).apply(
                        format_currency
                    )
                    df_to_save.to_csv("valores_dps.csv", sep=";", index=False)
                    st.success("Valores de DPS atualizados com sucesso.")

            with st.expander("🔩 Tabela de Preços Barra Pente", expanded=False):
                try:
                    df_barra_pente_raw = pd.read_csv("valores_barra_pente.csv", sep=";")
                    df_barra_pente_raw["Preco"] = (
                        df_barra_pente_raw["Preco"]
                        .astype(str)
                        .str.replace(r"R\$\s*", "", regex=True)
                        .str.replace(r"\.", "", regex=True)
                        .str.replace(",", ".", regex=True)
                        .pipe(pd.to_numeric, errors="coerce")
                        .fillna(0.0)
                    )
                except FileNotFoundError:
                    df_barra_pente_raw = pd.DataFrame(
                        [
                            ["Barra de pente BIF 12 Disj 80A", 22.00, ""],
                            ["Barra de pente TRI 12 Disj 80A", 34.00, ""],
                        ],
                        columns=["Material", "Preco", "Atualizado"],
                    )

                df_barra_pente_display = df_barra_pente_raw.copy()
                df_barra_pente_display["Preco"] = df_barra_pente_display["Preco"].apply(
                    format_currency
                )

                edited_barra_pente = st.data_editor(
                    df_barra_pente_display,
                    num_rows="dynamic",
                    key="valores_barra_pente_editor",
                    column_config={
                        "Material": st.column_config.TextColumn("Material"),
                        "Preco": st.column_config.TextColumn("Preço"),
                        "Atualizado": st.column_config.Column("Atualizado", disabled=True),
                    },
                )
                st.session_state["valores_barra_pente_df"] = edited_barra_pente

                if st.button("Salvar valores de barra pente"):
                    df_to_save = edited_barra_pente.copy()
                    df_original = df_barra_pente_raw.reindex(df_to_save.index)
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
                    df_to_save.loc[
                        alterado & df_to_save["Preco"].notna(), "Atualizado"
                    ] = hoje
                    df_to_save["Preco"] = df_to_save["Preco"].fillna(0.0).apply(
                        format_currency
                    )
                    df_to_save.to_csv("valores_barra_pente.csv", sep=";", index=False)
                    st.success("Valores de barra pente atualizados com sucesso.")

            with st.expander("🗄️ Tabela de Preços Paineis e Quadros", expanded=False):
                try:
                    df_paineis_quadros_raw = pd.read_csv(
                        "valores_paineis_quadros.csv", sep=";"
                    )
                    df_paineis_quadros_raw["Preco"] = (
                        df_paineis_quadros_raw["Preco"]
                        .astype(str)
                        .str.replace(r"R\$\s*", "", regex=True)
                        .str.replace(r"\.", "", regex=True)
                        .str.replace(",", ".", regex=True)
                        .pipe(pd.to_numeric, errors="coerce")
                        .fillna(0.0)
                    )
                except FileNotFoundError:
                    df_paineis_quadros_raw = pd.DataFrame(
                        [
                            ["Painel metalico 20x20x14", 89.00, ""],
                            ["Painel metalico 30×30×20", 178.58, ""],
                            ["Painel metalico 40×30×25", 199.72, ""],
                            ["Painel metalico 40×40×20", 187.21, ""],
                            ["Painel metalico 50×40×25", 240.77, ""],
                            ["Painel metalico 50×50×20", 377.06, ""],
                            ["Painel metalico 60×50×20", 338.93, ""],
                            ["Painel metalico 60×60×20", 558.37, ""],
                            ["Painel metalico 70×50×20", 474.62, ""],
                            ["Centro Sobre PVC P/08 DISJ", 68.00, ""],
                            ["Centro Sobre PVC P/012 DISJ", 73.00, ""],
                        ],
                        columns=["Material", "Preco", "Atualizado"],
                    )

                df_paineis_quadros_display = df_paineis_quadros_raw.copy()
                df_paineis_quadros_display["Preco"] = df_paineis_quadros_display[
                    "Preco"
                ].apply(format_currency)

                edited_paineis_quadros = st.data_editor(
                    df_paineis_quadros_display,
                    num_rows="dynamic",
                    key="valores_paineis_quadros_editor",
                    column_config={
                        "Material": st.column_config.TextColumn("Material"),
                        "Preco": st.column_config.TextColumn("Preço"),
                        "Atualizado": st.column_config.Column("Atualizado", disabled=True),
                    },
                )
                st.session_state["valores_paineis_quadros_df"] = edited_paineis_quadros

                if st.button("Salvar valores de paineis e quadros"):
                    df_to_save = edited_paineis_quadros.copy()
                    df_original = df_paineis_quadros_raw.reindex(df_to_save.index)
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
                    df_to_save.loc[
                        alterado & df_to_save["Preco"].notna(), "Atualizado"
                    ] = hoje
                    df_to_save["Preco"] = df_to_save["Preco"].fillna(0.0).apply(
                        format_currency
                    )
                    df_to_save.to_csv("valores_paineis_quadros.csv", sep=";", index=False)
                    st.success("Valores de paineis e quadros atualizados com sucesso.")

        with st.expander("📦 Material Adicional", expanded=False):

            with st.expander(
                "🧰 Tabela de Preços Disjuntor Caixa Moldada", expanded=False
            ):
                try:
                    df_disjuntores_raw = pd.read_csv(
                        "valores_disjuntor_caixa_moldada.csv", sep=";"
                    )
                    df_disjuntores_raw["Preco"] = (
                        df_disjuntores_raw["Preco"]
                        .astype(str)
                        .str.replace(r"R\$\s*", "", regex=True)
                        .str.replace(r"\.", "", regex=True)
                        .str.replace(",", ".", regex=True)
                        .pipe(pd.to_numeric, errors="coerce")
                        .fillna(0.0)
                    )
                except FileNotFoundError:
                    df_disjuntores_raw = pd.DataFrame(
                        [
                            ["440V EZC100N3100", "100A", "Schneider", 361.99, ""],
                            ["690VCA 3KA SDJS125", "125A", "Steck", 368.99, ""],
                            ["DWP250 20KA", "150A", "WEG", 434.90, ""],
                            ["400V20KA DWP250L1603", "160A", "WEG", 435.49, ""],
                            ["690VCA 3KA SDJS200", "200A", "Steck", 444.99, ""],
                            ["Asgard", "250A", "Steck", 512.54, ""],
                            ["690VCA 10KA SDJS300", "300A", "Steck", 891.78, ""],
                            ["690V 10KA", "350A", "Steck", 1106.99, ""],
                            ["690Vac/250Vdc 70KA SDJS400", "400A", "Steck", 1070.99, ""],
                            ["Asgard", "450A", "Steck", 2700.71, ""],
                            ["Asgard", "500A", "Steck", 2707.18, ""],
                            ["Asgard", "600A", "Steck", 2707.18, ""],
                        ],
                        columns=["Modelo", "Corrente", "Fabricante", "Preco", "Atualizado"],
                    )

                df_disjuntores_display = df_disjuntores_raw.copy()
                df_disjuntores_display["Preco"] = df_disjuntores_display["Preco"].apply(
                    format_currency
                )

                edited_disjuntores = st.data_editor(
                    df_disjuntores_display,
                    num_rows="dynamic",
                    key="valores_disjuntores_editor",
                    column_config={
                        "Preco": st.column_config.TextColumn("Preço"),
                        "Atualizado": st.column_config.Column("Atualizado", disabled=True),
                    },
                )
                st.session_state["valores_disjuntores_df"] = edited_disjuntores

                if st.button("Salvar valores de disjuntores", key="salvar_disjuntores"):
                    df_to_save = edited_disjuntores.copy()
                    df_original = df_disjuntores_raw.reindex(df_to_save.index)
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
                    df_to_save.loc[
                        alterado & df_to_save["Preco"].notna(), "Atualizado"
                    ] = hoje
                    df_to_save["Preco"] = df_to_save["Preco"].fillna(0.0).apply(
                        format_currency
                    )
                    df_to_save.to_csv(
                        "valores_disjuntor_caixa_moldada.csv", sep=";", index=False
                    )
                    st.success("Valores de disjuntores atualizados com sucesso.")

            with st.expander("🔩 Tabela de Preços Barra Roscada", expanded=False):
                try:
                    df_barra_roscada_raw = pd.read_csv(
                        "valores_barra_roscada.csv", sep=";"
                    )
                    df_barra_roscada_raw["Preco"] = (
                        df_barra_roscada_raw["Preco"]
                        .astype(str)
                        .str.replace(r"R\$\s*", "", regex=True)
                        .str.replace(r"\.", "", regex=True)
                        .str.replace(",", ".", regex=True)
                        .pipe(pd.to_numeric, errors="coerce")
                        .fillna(0.0)
                    )
                except FileNotFoundError:
                    df_barra_roscada_raw = pd.DataFrame(
                        [["Barra Roscada 1/4", 16.00, ""]],
                        columns=["Material", "Preco", "Atualizado"],
                    )

                df_barra_roscada_display = df_barra_roscada_raw.copy()
                df_barra_roscada_display["Preco"] = df_barra_roscada_display["Preco"].apply(
                    format_currency
                )

                edited_barra_roscada = st.data_editor(
                    df_barra_roscada_display,
                    num_rows="dynamic",
                    key="valores_barra_roscada_editor",
                    column_config={
                        "Material": st.column_config.TextColumn("Material"),
                        "Preco": st.column_config.TextColumn("Preço"),
                        "Atualizado": st.column_config.Column("Atualizado", disabled=True),
                    },
                )
                st.session_state["valores_barra_roscada_df"] = edited_barra_roscada

                if st.button(
                    "Salvar valores de barra roscada", key="salvar_barra_roscada"
                ):
                    df_to_save = edited_barra_roscada.copy()
                    df_original = df_barra_roscada_raw.reindex(df_to_save.index)
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
                    df_to_save.loc[
                        alterado & df_to_save["Preco"].notna(), "Atualizado"
                    ] = hoje
                    df_to_save["Preco"] = df_to_save["Preco"].fillna(0.0).apply(
                        format_currency
                    )
                    df_to_save.to_csv("valores_barra_roscada.csv", sep=";", index=False)
                    st.success("Valores de barra roscada atualizados com sucesso.")

            with st.expander("📋 Tabela de Preços Eletrocalhas", expanded=False):
                try:
                    df_eletrocalhas_raw = pd.read_csv(
                        "valores_eletrocalhas.csv", sep=";"
                    )
                    if "Atualizado" not in df_eletrocalhas_raw.columns:
                        df_eletrocalhas_raw["Atualizado"] = ""
                    df_eletrocalhas_raw["Preco"] = (
                        df_eletrocalhas_raw["Preco"]
                        .astype(str)
                        .str.replace(r"R\$\s*", "", regex=True)
                        .str.replace(r"\.", "", regex=True)
                        .str.replace(",", ".", regex=True)
                        .pipe(pd.to_numeric, errors="coerce")
                        .fillna(0.0)
                    )
                except FileNotFoundError:
                    eletrocalhas_data = [
                        {"Material": "Eletrocalha perfurada #24 50x50mm", "Preco": 36.00},
                        {"Material": "Eletrocalha perfurada #24 75x50mm", "Preco": 49.82},
                        {"Material": "Eletrocalha perfurada #24 75x75mm", "Preco": 50.00},
                        {"Material": "Eletrocalha perfurada #24 100x75mm", "Preco": 69.88},
                        {"Material": "Eletrocalha perfurada #24 100x100mm", "Preco": 74.20},
                        {"Material": "Eletrocalha perfurada #24 150x100mm", "Preco": 86.36},
                        {"Material": "Eletrocalha perfurada #24 200x100mm", "Preco": 92.08},
                        {"Material": "Eletrocalha perfurada #24 250x100mm", "Preco": 142.39},
                        {"Material": "Eletrocalha perfurada #24 300x100mm", "Preco": 150.00},
                    ]
                    df_eletrocalhas_raw = pd.DataFrame(eletrocalhas_data)
                    df_eletrocalhas_raw["Atualizado"] = ""

                df_eletrocalhas_display = df_eletrocalhas_raw.copy()
                df_eletrocalhas_display["Preco"] = df_eletrocalhas_display["Preco"].apply(
                    format_currency
                )

                edited_eletrocalhas = st.data_editor(
                    df_eletrocalhas_display,
                    num_rows="dynamic",
                    key="valores_eletrocalhas_editor",
                    column_config={
                        "Material": st.column_config.TextColumn("Material"),
                        "Preco": st.column_config.TextColumn("Preço"),
                        "Atualizado": st.column_config.Column("Atualizado", disabled=True),
                    },
                )
                st.session_state["valores_eletrocalhas_df"] = edited_eletrocalhas

                if st.button(
                    "Salvar valores de eletrocalhas", key="salvar_eletrocalhas"
                ):
                    df_to_save = edited_eletrocalhas.copy()
                    df_original = df_eletrocalhas_raw.reindex(df_to_save.index)
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
                    df_to_save.loc[
                        alterado & df_to_save["Preco"].notna(), "Atualizado"
                    ] = hoje
                    df_to_save["Preco"] = df_to_save["Preco"].fillna(0.0).apply(
                        format_currency
                    )
                    df_to_save.to_csv("valores_eletrocalhas.csv", sep=";", index=False)
                    st.success("Valores de eletrocalhas atualizados com sucesso.")

            with st.expander("🔌 Tabela de Preços Tomada Industrial", expanded=False):
                try:
                    df_tomadas_industriais_raw = pd.read_csv(
                        "valores_tomadas_industriais.csv", sep=";"
                    )
                    if "Atualizado" not in df_tomadas_industriais_raw.columns:
                        df_tomadas_industriais_raw["Atualizado"] = ""
                    df_tomadas_industriais_raw["Preco"] = (
                        df_tomadas_industriais_raw["Preco"]
                        .astype(str)
                        .str.replace(r"R\$\s*", "", regex=True)
                        .str.replace(r"\.", "", regex=True)
                        .str.replace(",", ".", regex=True)
                        .pipe(pd.to_numeric, errors="coerce")
                        .fillna(0.0)
                    )
                except FileNotFoundError:
                    tomadas_industriais_data = [
                        {
                            "Material": "Tomada Sobrepor Industrial 16A 2P+T 6h (Azul)",
                            "Preco": 64.79,
                        },
                        {
                            "Material": "Tomada Sobrepor Industrial 32A 2P+T 6h (Azul)",
                            "Preco": 70.00,
                        },
                        {
                            "Material": "Tomada Sobrepor 3p+T+N 32A 6h (Verm.)",
                            "Preco": 150.00,
                        },
                    ]
                    df_tomadas_industriais_raw = pd.DataFrame(
                        tomadas_industriais_data
                    )
                    df_tomadas_industriais_raw["Atualizado"] = ""

                df_tomadas_industriais_display = df_tomadas_industriais_raw.copy()
                df_tomadas_industriais_display["Preco"] = (
                    df_tomadas_industriais_display["Preco"].apply(format_currency)
                )

                edited_tomadas_industriais = st.data_editor(
                    df_tomadas_industriais_display,
                    num_rows="dynamic",
                    key="valores_tomadas_industriais_editor",
                    column_config={
                        "Material": st.column_config.TextColumn("Material"),
                        "Preco": st.column_config.TextColumn("Preço"),
                        "Atualizado": st.column_config.Column("Atualizado", disabled=True),
                    },
                )
                st.session_state["valores_tomadas_industriais_df"] = (
                    edited_tomadas_industriais
                )

                if st.button(
                    "Salvar valores de tomadas industriais",
                    key="salvar_tomadas_industriais",
                ):
                    df_to_save = edited_tomadas_industriais.copy()
                    df_original = df_tomadas_industriais_raw.reindex(df_to_save.index)
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
                    df_to_save.loc[
                        alterado & df_to_save["Preco"].notna(), "Atualizado"
                    ] = hoje
                    df_to_save["Preco"] = df_to_save["Preco"].fillna(0.0).apply(
                        format_currency
                    )
                    df_to_save.to_csv(
                        "valores_tomadas_industriais.csv", sep=";", index=False
                    )
                    st.success(
                        "Valores de tomadas industriais atualizados com sucesso."
                    )

            with st.expander("📟 Tabela de Preços Medidores", expanded=False):
                try:
                    df_medidores_raw = pd.read_csv("valores_medidores.csv", sep=";")
                    if "Atualizado" not in df_medidores_raw.columns:
                        df_medidores_raw["Atualizado"] = ""
                    df_medidores_raw["Preco"] = (
                        df_medidores_raw["Preco"]
                        .astype(str)
                        .str.replace(r"R\$\s*", "", regex=True)
                        .str.replace(r"\.", "", regex=True)
                        .str.replace(",", ".", regex=True)
                        .pipe(pd.to_numeric, errors="coerce")
                        .fillna(0.0)
                    )
                except FileNotFoundError:
                    medidores_data = [
                        {"Material": "Medidor Bipolar Wifi", "Preco": 229.00},
                        {"Material": "Medidor Bipolar", "Preco": 349.50},
                    ]
                    df_medidores_raw = pd.DataFrame(medidores_data)
                    df_medidores_raw["Atualizado"] = ""

                df_medidores_display = df_medidores_raw.copy()
                df_medidores_display["Preco"] = df_medidores_display["Preco"].apply(
                    format_currency
                )

                edited_medidores = st.data_editor(
                    df_medidores_display,
                    num_rows="dynamic",
                    key="valores_medidores_editor",
                    column_config={
                        "Material": st.column_config.TextColumn("Material"),
                        "Preco": st.column_config.TextColumn("Preço"),
                        "Atualizado": st.column_config.Column("Atualizado", disabled=True),
                    },
                )
                st.session_state["valores_medidores_df"] = edited_medidores

                if st.button("Salvar valores de medidores", key="salvar_medidores"):
                    df_to_save = edited_medidores.copy()
                    df_original = df_medidores_raw.reindex(df_to_save.index)
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
                    df_to_save.loc[
                        alterado & df_to_save["Preco"].notna(), "Atualizado"
                    ] = hoje
                    df_to_save["Preco"] = df_to_save["Preco"].fillna(0.0).apply(
                        format_currency
                    )
                    df_to_save.to_csv("valores_medidores.csv", sep=";", index=False)
                    st.success("Valores de medidores atualizados com sucesso.")

            with st.expander("⚡ Tabela de Preços de Transformadores", expanded=False):
                transformadores_data = obter_transformadores_padrao()

                df_transformadores = pd.DataFrame(transformadores_data)
                df_transformadores["Preço"] = df_transformadores["Preço"].apply(
                    format_currency
                )
                st.session_state["transformadores_produtos"] = (
                    df_transformadores["Produto"].dropna().tolist()
                )
                st.table(df_transformadores)
