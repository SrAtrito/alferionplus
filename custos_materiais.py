import streamlit as st
import pandas as pd
import re
import math
import unicodedata
from typing import Optional
from collections.abc import Mapping
from io import BytesIO

from Deslocamento import calcula_custo_deslocamento
from dados_transformadores import obter_transformadores_padrao
from grafico_custos_materiais import render_pizza_custos_materiais


def _load_editor_dataframe(state_key: str):
    """Retrieve and normalize a DataFrame stored in session_state."""
    raw = st.session_state.get(state_key)
    if raw is None:
        return None
    if isinstance(raw, pd.DataFrame):
        return raw
    if isinstance(raw, list):
        return pd.DataFrame(raw)
    if isinstance(raw, Mapping):
        if "data" in raw and "columns" in raw:
            return pd.DataFrame(raw["data"], columns=raw["columns"])
        normalized = {
            k: list(v.values()) if isinstance(v, Mapping) else v
            for k, v in raw.items()
        }
        return pd.DataFrame(normalized)
    return pd.DataFrame(raw)


def render_custos_materiais_tab(tab_resumo, format_currency):
    """Renderiza a aba 'Custos com Materiais'."""
    with tab_resumo:
        def _parse_bitola(valor):
            """Extrai o valor numérico de uma bitola, retornando 0 se inválido."""
            match = re.search(r"(\d+(?:[.,]\d+)?)", str(valor))
            return float(match.group(1).replace(",", ".")) if match else 0.0

        def _parse_float_field(valor):
            """Converte um campo textual em float, aceitando formatos de moeda."""
            if valor is None:
                return 0.0
            if isinstance(valor, (int, float)):
                return float(valor)
            texto = str(valor).strip()
            if not texto:
                return 0.0
            texto = (
                texto.replace("R$", "")
                .replace("r$", "")
                .replace("\u00a0", "")
                .strip()
            )
            texto = re.sub(r"[^0-9,.-]", "", texto)
            if "," in texto and "." in texto:
                texto = texto.replace(".", "").replace(",", ".")
            else:
                texto = texto.replace(",", ".")
            try:
                return float(texto)
            except ValueError:
                return 0.0

        def _load_price_table(session_key, editor_key, csv_path, fallback_rows=None):
            """Carrega uma tabela de preços considerando sessão, editor e arquivo CSV."""

            df_preco = st.session_state.get(session_key)
            if df_preco is None and editor_key:
                df_preco = _load_editor_dataframe(editor_key)

            if df_preco is None:
                try:
                    df_preco = pd.read_csv(csv_path, sep=";")
                except FileNotFoundError:
                    if fallback_rows is None:
                        return pd.DataFrame()
                    df_preco = pd.DataFrame(fallback_rows)
            else:
                df_preco = pd.DataFrame(df_preco)

            if not isinstance(df_preco, pd.DataFrame):
                df_preco = pd.DataFrame(df_preco)

            def _find_price_column(columns: pd.Index) -> Optional[str]:
                for coluna in columns:
                    nome_normalizado = (
                        unicodedata.normalize("NFKD", str(coluna))
                        .encode("ASCII", "ignore")
                        .decode("ASCII")
                        .lower()
                    )
                    if "preco" in nome_normalizado or "preço" in nome_normalizado:
                        return coluna
                return None

            coluna_preco = _find_price_column(df_preco.columns)

            if coluna_preco:
                df_preco["_PrecoNumerico"] = df_preco[coluna_preco].apply(
                    _parse_float_field
                )
            elif "_PrecoNumerico" not in df_preco.columns:
                df_preco["_PrecoNumerico"] = 0.0

            if "Preco" not in df_preco.columns and "_PrecoNumerico" in df_preco.columns:
                df_preco["Preco"] = df_preco["_PrecoNumerico"]

            return df_preco

        def _sync_selectbox_state(target_key: str, source_key: str, options: list[str], default: str = "") -> str:
            """Mantém o valor de um selectbox alinhado ao valor vindo do resumo."""

            source_value = st.session_state.get(source_key, default)
            if source_value is None:
                source_value = default
            if source_value == "":
                if "" not in options:
                    options.insert(0, "")
            elif source_value not in options:
                options.append(source_value)

            ref_key = f"{target_key}_source_ref"
            if st.session_state.get(ref_key) != source_value:
                st.session_state[target_key] = source_value
                st.session_state[ref_key] = source_value

            return source_value

        def _create_selectbox_sync_callback(widget_key: str, source_key: str):
            """Retorna um callback que sincroniza o widget com a chave de origem."""

            def _callback():
                selected_value = st.session_state.get(widget_key, "")
                st.session_state[source_key] = selected_value
                st.session_state[f"{widget_key}_source_ref"] = selected_value

            return _callback

        possui_carregador = st.session_state.get("possui_carregador", "")

        if possui_carregador == "Não":
            with st.expander("⚡ Custo Carregador", expanded=True):
                tabela_precos_ce = _load_price_table(
                    "tabela_precos_ce_df",
                    "tabela_precos_ce_editor",
                    "tabela_precos_ce.csv",
                )

                if tabela_precos_ce.empty:
                    st.info(
                        "Cadastre os carregadores na tabela 'Tabela Preços de CE' na aba"
                        " 'Valores de CE' para habilitar a seleção."
                    )
                else:
                    tabela_precos_ce = tabela_precos_ce.fillna("")

                    opcoes_carregadores: list[str] = []
                    dados_carregadores: dict[str, dict[str, object]] = {}

                    for _, linha in tabela_precos_ce.iterrows():
                        fabricante = str(linha.get("Fabricante", "")).strip()
                        modelo = str(linha.get("Modelo", "")).strip()
                        potencia = str(linha.get("Potência", "")).strip()
                        tensao = str(linha.get("Tensão", "")).strip()
                        carga = str(linha.get("Carga", "")).strip()
                        conector = str(linha.get("Conector", "")).strip()
                        preco_num = float(linha.get("_PrecoNumerico", 0.0) or 0.0)
                        preco_exibicao = format_currency(preco_num)

                        titulo = " - ".join(
                            [texto for texto in [fabricante, modelo] if texto]
                        )
                        detalhes = " | ".join(
                            [
                                texto
                                for texto in [potencia, tensao, carga, conector]
                                if texto
                            ]
                        )
                        if detalhes:
                            titulo = f"{titulo} ({detalhes})" if titulo else detalhes
                        if not titulo:
                            continue

                        rotulo = f"{titulo} - {preco_exibicao}"
                        if rotulo in dados_carregadores:
                            continue

                        dados_carregadores[rotulo] = {
                            "Fabricante": fabricante,
                            "Modelo": modelo,
                            "Potência": potencia,
                            "Tensão": tensao,
                            "Carga": carga,
                            "Conector": conector,
                            "Preço": preco_num,
                        }
                        opcoes_carregadores.append(rotulo)

                    if not opcoes_carregadores:
                        st.info(
                            "Nenhum carregador válido encontrado na tabela de preços de CE."
                        )
                    else:
                        escolha_atual = st.session_state.get(
                            "carregador_ce_rotulo", opcoes_carregadores[0]
                        )
                        if escolha_atual not in opcoes_carregadores:
                            escolha_atual = opcoes_carregadores[0]

                        carregador_selecionado = st.selectbox(
                            "Escolha o carregador",
                            options=opcoes_carregadores,
                            index=opcoes_carregadores.index(escolha_atual),
                            key="carregador_ce_rotulo",
                        )

                        dados_selecionados = dados_carregadores.get(
                            carregador_selecionado, {}
                        )

                        if dados_selecionados:
                            st.session_state["carregador_ce_dados"] = dados_selecionados
                            st.session_state["potencia_carregador_orcamento"] = (
                                dados_selecionados.get("Potência", "")
                            )
                            st.session_state["tensao_carregador_orcamento"] = (
                                dados_selecionados.get("Tensão", "")
                            )
                            st.session_state["preco_carregador_orcamento"] = (
                                dados_selecionados.get("Preço", 0.0)
                            )

                            st.markdown(
                                "\n".join(
                                    [
                                        f"**Fabricante:** {dados_selecionados.get('Fabricante', '')}",
                                        f"**Modelo:** {dados_selecionados.get('Modelo', '')}",
                                        f"**Potência:** {dados_selecionados.get('Potência', '')}",
                                        f"**Tensão:** {dados_selecionados.get('Tensão', '')}",
                                        f"**Carga:** {dados_selecionados.get('Carga', '')}",
                                        f"**Conector:** {dados_selecionados.get('Conector', '')}",
                                        f"**Preço:** {format_currency(dados_selecionados.get('Preço', 0.0))}",
                                    ]
                                )
                            )
        else:
            st.session_state.pop("carregador_ce_dados", None)
            st.session_state.pop("carregador_ce_rotulo", None)
            st.session_state.pop("potencia_carregador_orcamento", None)
            st.session_state.pop("tensao_carregador_orcamento", None)
            st.session_state.pop("preco_carregador_orcamento", None)

        with st.expander("🔌 Custo com Cabos", expanded=True):

            percursos = st.session_state.get("percursos", [])
            soma_distancias = sum(trecho for _, trecho in percursos)
    
            bitola_fase1 = st.session_state.get("bitola_sugerida", "")
            bitola_fase1_val = _parse_bitola(bitola_fase1)
            bitola_neutro = st.session_state.get("bitola_neutro_sugerida", "")
            bitola_neutro_val = _parse_bitola(bitola_neutro)
            bitola_terra = st.session_state.get("bitola_terra_sugerida", "")
            bitola_terra_val = _parse_bitola(bitola_terra)
            instalacao = st.session_state.get("instalacao_sistema", "")
    
            if bitola_fase1_val > 0:
                quantidade_preto = {
                    "Monofásico": 1,
                    "Bifásico": 2,
                    "Trifásico": 3,
                }.get(instalacao, 1)
            else:
                quantidade_preto = 0
            quantidade_azul = 1 if bitola_neutro_val > 0 and instalacao != "Bifásico" else 0
            quantidade_verde = 1 if bitola_terra_val > 0 else 0
    
            metragem_cabo_preto = soma_distancias * quantidade_preto
            metragem_cabo_azul = soma_distancias * quantidade_azul
            metragem_cabo_verde = soma_distancias * quantidade_verde
    
            # --- Tabela de quantidade e custo dos cabos ---
            df_cabos_preco = st.session_state.get("valores_cabos_df")
            if df_cabos_preco is None:
                df_cabos_preco = _load_editor_dataframe("valores_cabos_editor")
            if df_cabos_preco is None:
                try:
                    df_cabos_preco = pd.read_csv("valores_cabos.csv", sep=";")
                except FileNotFoundError:
                    df_cabos_preco = pd.DataFrame()
    
            # Define colunas de cabo e preço conforme o tipo selecionado
            tipo_cabos = st.session_state.get("tipo_cabos", "")
            tipo_cabo_label = (
                "HEPR" if "HEPR" in str(tipo_cabos).upper() else "PVC"
            )
            col_cabo = "Cabo 750V"
            col_preco = "Preco 750V"
            if tipo_cabo_label == "HEPR":
                col_cabo = "Cabo 1kV"
                col_preco = "Preco 1kV"
    
            cabos_dados = []
            if not df_cabos_preco.empty:
                for col in ["Preco 750V", "Preco 1kV"]:
                    df_cabos_preco[col] = (
                        df_cabos_preco[col]
                        .astype(str)
                        .str.replace(r"R\$\s*", "", regex=True)
                        .str.replace(r"\.", "", regex=True)
                        .str.replace(",", ".", regex=True)
                        .pipe(pd.to_numeric, errors="coerce")
                        .fillna(0.0)
                    )
                df_cabos_preco["bitola"] = (
                    df_cabos_preco[col_cabo]
                    .astype(str)
                    .str.extract(r"(\d+(?:[.,]\d+)?)\s*mm")[0]
                    .str.replace(",", ".")
                    .astype(float)
                )
    
            def _obter_preco(bitola_val: float) -> float:
                preco_unit = 0.0
                if bitola_val > 0 and not df_cabos_preco.empty:
                    preco_match = df_cabos_preco.loc[
                        df_cabos_preco["bitola"] == bitola_val, col_preco
                    ]
                    if not preco_match.empty:
                        preco_unit = float(preco_match.iloc[0])
                return preco_unit
    
            preco_preto = _obter_preco(bitola_fase1_val)
            preco_azul = _obter_preco(bitola_neutro_val)
            preco_verde = _obter_preco(bitola_terra_val)
    
            total_cabos_valor = 0.0
    
            if quantidade_preto > 0:
                total_preto = preco_preto * metragem_cabo_preto
                total_cabos_valor += total_preto
                cabos_dados.append(
                    {
                        "Item": f"Cabo Preto {tipo_cabo_label}",
                        "Bitola (mm²)": bitola_fase1,
                        "Valor Unitário": format_currency(preco_preto),
                        "Quantidade (m)": f"{metragem_cabo_preto:.2f}",
                        "Total": format_currency(total_preto),
                    }
                )
            if quantidade_azul > 0:
                total_azul = preco_azul * metragem_cabo_azul
                total_cabos_valor += total_azul
                cabos_dados.append(
                    {
                        "Item": f"Cabo Azul {tipo_cabo_label}",
                        "Bitola (mm²)": bitola_neutro,
                        "Valor Unitário": format_currency(preco_azul),
                        "Quantidade (m)": f"{metragem_cabo_azul:.2f}",
                        "Total": format_currency(total_azul),
                    }
                )
            if quantidade_verde > 0:
                total_verde = preco_verde * metragem_cabo_verde
                total_cabos_valor += total_verde
                cabos_dados.append(
                    {
                        "Item": f"Cabo Verde {tipo_cabo_label}",
                        "Bitola (mm²)": bitola_terra,
                        "Valor Unitário": format_currency(preco_verde),
                        "Quantidade (m)": f"{metragem_cabo_verde:.2f}",
                        "Total": format_currency(total_verde),
                    }
                )
    
            tabela_cabos = pd.DataFrame(cabos_dados)
            st.table(tabela_cabos)
            if total_cabos_valor > 0:
                st.write(f"Total: {format_currency(total_cabos_valor)}")
        with st.expander("🏗️ Custo com Infra-Seca", expanded=False):
    
            tamanho_eletroduto_raw = str(
                st.session_state.get("tamanho_eletroduto", "")
            )
            tamanho_eletroduto = re.sub(
                r'["\u201d]', "", tamanho_eletroduto_raw
            ).strip()
    
            df_eletrodutos_preco = st.session_state.get("valores_eletrodutos_df")
            if df_eletrodutos_preco is None:
                df_eletrodutos_preco = _load_editor_dataframe(
                    "valores_eletrodutos_editor"
                )
            if df_eletrodutos_preco is None:
                try:
                    df_eletrodutos_preco = pd.read_csv("valores_eletrodutos.csv", sep=";")
                except FileNotFoundError:
                    df_eletrodutos_preco = pd.DataFrame()
    
            if not df_eletrodutos_preco.empty:
                df_eletrodutos_preco["Categoria"] = (
                    df_eletrodutos_preco["Categoria"]
                    .astype(str)
                    .str.replace("\u201d", "", regex=False)
                    .str.replace('"', "", regex=False)
                    .str.strip()
                )
                df_eletrodutos_preco["Preco"] = (
                    df_eletrodutos_preco["Preco"]
                    .astype(str)
                    .str.replace(r"R\$\s*", "", regex=True)
                    .str.replace(r"\.", "", regex=True)
                    .str.replace(",", ".", regex=True)
                    .pipe(pd.to_numeric, errors="coerce")
                    .fillna(0.0)
                )
    
            df_sealtubo_preco = st.session_state.get("valores_sealtubo_df")
            if df_sealtubo_preco is None:
                df_sealtubo_preco = pd.DataFrame(
                    {
                        "Sealtubo": [
                            f"Sealtubo com capa {t}\""
                            for t in ["3/4", "1", "1 1/4", "1 1/2", "2"]
                        ],
                        "Preco": [8.70, 10.69, 17.28, 19.65, 26.31],
                    }
                )
            if not df_sealtubo_preco.empty:
                df_sealtubo_preco["Sealtubo"] = (
                    df_sealtubo_preco["Sealtubo"]
                    .astype(str)
                    .str.replace("\u201d", "", regex=False)
                    .str.replace('"', "", regex=False)
                    .str.strip()
                )
                df_sealtubo_preco["Preco"] = (
                    df_sealtubo_preco["Preco"]
                    .astype(str)
                    .str.replace(r"R\$\s*", "", regex=True)
                    .apply(lambda x: x.replace(".", "").replace(",", ".") if "," in x else x)
                    .pipe(pd.to_numeric, errors="coerce")
                    .fillna(0.0)
                )
            def _obter_eletroduto_info(tamanho: str) -> tuple[str, float]:
                tamanho = re.sub(r'["\u201d]', "", str(tamanho)).strip()
                if tamanho and not df_eletrodutos_preco.empty:
                    categoria = f"Eletroduto de {tamanho}"
                    linha = df_eletrodutos_preco.loc[
                        (df_eletrodutos_preco["Categoria"] == categoria)
                        & (
                            df_eletrodutos_preco["Material"].str.contains(
                                "Eletroduto Galv Pre-Zinc", case=False
                            )
                        )
                    ]
                    if not linha.empty:
                        material = re.sub(
                            r'["\u201d]', "", str(linha.iloc[0]["Material"])
                        ).strip()
                        preco = float(linha.iloc[0]["Preco"])
                        return material, preco
                return "", 0.0
    
            def _obter_condulete_info(tamanho: str) -> tuple[str, float]:
                tamanho = re.sub(r'["\u201d]', "", str(tamanho)).strip()
                if tamanho and not df_eletrodutos_preco.empty:
                    categoria = f"Eletroduto de {tamanho}"
                    linha = df_eletrodutos_preco.loc[
                        (df_eletrodutos_preco["Categoria"] == categoria)
                        & (
                            df_eletrodutos_preco["Material"].str.contains(
                                "Condulete s/rosca", case=False
                            )
                        )
                        & (
                            df_eletrodutos_preco["Material"].str.contains(
                                r"(?:C|LL|LR|X)$", case=False, regex=True
                            )
                        )
                    ]
                    if not linha.empty:
                        material = f"Condulete s/rosca {tamanho} C/LL/LR/X"
                        preco = float(linha.iloc[0]["Preco"])
                        return material, preco
                return "", 0.0
    
            def _obter_condulete_t_info(tamanho: str) -> tuple[str, float]:
                tamanho = re.sub(r'["\u201d]', "", str(tamanho)).strip()
                if tamanho and not df_eletrodutos_preco.empty:
                    categoria = f"Eletroduto de {tamanho}"
                    linha = df_eletrodutos_preco.loc[
                        (df_eletrodutos_preco["Categoria"] == categoria)
                        & (
                            df_eletrodutos_preco["Material"].str.contains(
                                "Condulete s/rosca", case=False
                            )
                        )
                        & (
                            df_eletrodutos_preco["Material"].str.contains(
                                r"T$", case=False, regex=True
                            )
                        )
                    ]
                    if not linha.empty:
                        material = f"Condulete s/rosca {tamanho} T"
                        preco = float(linha.iloc[0]["Preco"])
                        return material, preco
                return "", 0.0
    
            def _obter_unidut_reto_info(tamanho: str) -> tuple[str, float]:
                tamanho = re.sub(r'["\u201d]', "", str(tamanho)).strip()
                if tamanho and not df_eletrodutos_preco.empty:
                    categoria = f"Eletroduto de {tamanho}"
                    linha = df_eletrodutos_preco.loc[
                        (df_eletrodutos_preco["Categoria"] == categoria)
                        & (
                            df_eletrodutos_preco["Material"].str.contains(
                                "Unidut Reto comum", case=False
                            )
                        )
                    ]
                    if not linha.empty:
                        material = re.sub(
                            r'["\u201d]', "", str(linha.iloc[0]["Material"])
                        ).strip()
                        preco = float(linha.iloc[0]["Preco"])
                        return material, preco
                return "", 0.0
    
            def _obter_unidut_info(tamanho: str) -> tuple[str, float]:
                tamanho = re.sub(r'["\u201d]', "", str(tamanho)).strip()
                if tamanho and not df_eletrodutos_preco.empty:
                    categoria = f"Eletroduto de {tamanho}"
                    linha = df_eletrodutos_preco.loc[
                        (df_eletrodutos_preco["Categoria"] == categoria)
                        & (
                            df_eletrodutos_preco["Material"].str.contains(
                                "Unidut Conico comum", case=False
                            )
                        )
                    ]
                    if not linha.empty:
                        material = re.sub(
                            r'["\u201d]', "", str(linha.iloc[0]["Material"])
                        ).strip()
                        preco = float(linha.iloc[0]["Preco"])
                        return material, preco
                return "", 0.0
    
            def _obter_unilet_info(tamanho: str) -> tuple[str, float]:
                tamanho = re.sub(r'["\u201d]', "", str(tamanho)).strip()
                if tamanho and not df_eletrodutos_preco.empty:
                    categoria = f"Eletroduto de {tamanho}"
                    linha = df_eletrodutos_preco.loc[
                        (df_eletrodutos_preco["Categoria"] == categoria)
                        & (
                            df_eletrodutos_preco["Material"].str.contains(
                                "Unilet comum 90º", case=False
                            )
                        )
                    ]
                    if not linha.empty:
                        material = re.sub(
                            r'["\u201d]', "", str(linha.iloc[0]["Material"])
                        ).strip()
                        preco = float(linha.iloc[0]["Preco"])
                        return material, preco
                return "", 0.0
    
            def _obter_curva_galv_info(tamanho: str) -> tuple[str, float]:
                tamanho = re.sub(r'["\u201d]', "", str(tamanho)).strip()
                if tamanho and not df_eletrodutos_preco.empty:
                    categoria = f"Eletroduto de {tamanho}"
                    linha = df_eletrodutos_preco.loc[
                        (df_eletrodutos_preco["Categoria"] == categoria)
                        & (
                            df_eletrodutos_preco["Material"].str.contains(
                                r"Curva Galv Eletro\s*90º", case=False, regex=True
                            )
                        )
                    ]
                    if not linha.empty:
                        material = re.sub(
                            r'["\u201d]', "", str(linha.iloc[0]["Material"])
                        ).strip()
                        preco = float(linha.iloc[0]["Preco"])
                        return material, preco
                return "", 0.0
    
            def _obter_abracadeira_info(tamanho: str) -> tuple[str, float]:
                tamanho = re.sub(r'["\u201d]', "", str(tamanho)).strip()
                if tamanho and not df_eletrodutos_preco.empty:
                    categoria = f"Eletroduto de {tamanho}"
                    linha = df_eletrodutos_preco.loc[
                        (df_eletrodutos_preco["Categoria"] == categoria)
                        & (
                            df_eletrodutos_preco["Material"].str.contains(
                                "Abraçadeira D e cunha", case=False
                            )
                        )
                    ]
                    if not linha.empty:
                        material = re.sub(
                            r'["\u201d]', "", str(linha.iloc[0]["Material"])
                        ).strip()
                        preco = float(linha.iloc[0]["Preco"])
                        return material, preco
                return "", 0.0
    
            def _obter_sealtubo_info(tamanho: str) -> tuple[str, float]:
                tamanho = re.sub(r'["\u201d]', "", str(tamanho)).strip()
                if tamanho and not df_sealtubo_preco.empty:
                    linha = df_sealtubo_preco.loc[
                        df_sealtubo_preco["Sealtubo"].str.contains(tamanho)
                    ]
                    if not linha.empty:
                        material = re.sub(
                            r'["\u201d]', "", str(linha.iloc[0]["Sealtubo"])
                        ).strip()
                        preco = float(linha.iloc[0]["Preco"])
                        return material, preco
                return "", 0.0
    
            material_eletroduto, preco_eletroduto = _obter_eletroduto_info(
                tamanho_eletroduto
            )
            material_sealtubo, preco_sealtubo = _obter_sealtubo_info(
                tamanho_eletroduto
            )
            material_curva, preco_curva = _obter_curva_galv_info(
                tamanho_eletroduto
            )
            material_condulete, preco_condulete = _obter_condulete_info(
                tamanho_eletroduto
            )
            material_condulete_t, preco_condulete_t = _obter_condulete_t_info(
                tamanho_eletroduto
            )
            material_unidut_reto, preco_unidut_reto = _obter_unidut_reto_info(
                tamanho_eletroduto
            )
            material_unidut_conico, preco_unidut_conico = _obter_unidut_info(
                tamanho_eletroduto
            )
            material_unilet, preco_unilet = _obter_unilet_info(
                tamanho_eletroduto
            )
            material_abracadeira, preco_abracadeira = _obter_abracadeira_info(
                tamanho_eletroduto
            )

            custos_campos = [
                ("custo_eletrodutos", material_eletroduto),
                ("custo_condulete", material_condulete),
                ("custo_condulete_t", material_condulete_t),
                ("custo_unidut_reto", material_unidut_reto),
                ("custo_unidut_conico", material_unidut_conico),
                ("custo_curva_galv_eletro_90", material_curva),
                ("custo_unilet", material_unilet),
                ("custo_abracadeira", material_abracadeira),
                ("custo_sealtubo", material_sealtubo),
            ]

            def _definir_quantidade_padrao(chave: str, sugestao: str) -> None:
                sugestao_str = "" if sugestao is None else str(sugestao)
                valor_atual = st.session_state.get(chave, "")
                ultima_sugestao_key = f"{chave}_ultima_sugestao"
                ultima_sugestao = st.session_state.get(ultima_sugestao_key)

                valor_limpo = str(valor_atual).strip()
                sugestao_limpa = sugestao_str.strip()
                ultima_limpa = (
                    "" if ultima_sugestao is None else str(ultima_sugestao).strip()
                )

                atualizar_padrao = False
                if ultima_sugestao is None:
                    if (
                        valor_limpo in ("", "0", "0.0")
                        and sugestao_limpa not in ("", "0", "0.0")
                    ):
                        atualizar_padrao = True
                elif valor_limpo == ultima_limpa and sugestao_limpa != ultima_limpa:
                    atualizar_padrao = True

                if atualizar_padrao:
                    st.session_state[chave] = sugestao_str

                st.session_state[ultima_sugestao_key] = sugestao_str

            def _sincronizar_campos_custos() -> None:
                for key, value in custos_campos:
                    st.session_state[key] = value or ""

            _sincronizar_campos_custos()

            st.markdown(
                """
                <style>
                div[data-testid="stTextInput"] input[aria-label="Custo Eletrodutos"] {
                    font-size: 24px;
                    font-weight: bold;
                    background-color: #ffffff;
                    color: #000000;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='font-size:24px; font-weight:bold;'>Custo Eletrodutos</p>",
                unsafe_allow_html=True,
            )
            _sincronizar_campos_custos()
            st.text_input(
                "Custo Eletrodutos",
                value=st.session_state.get("custo_eletrodutos", ""),
                key="custo_eletrodutos",
                disabled=True,
                label_visibility="collapsed",
            )
    
            metragem_sugerida = soma_distancias
            quantidade_eletrodutos = (
                math.ceil(metragem_sugerida / 3) if metragem_sugerida else 0
            )
            col_sug, col_qtd_label, col_qtd_input, col_total = st.columns([1, 1, 2, 1])
            quantidade_eletrodutos_sugestao = f"{quantidade_eletrodutos}"
            _definir_quantidade_padrao(
                "quantidade_eletroduto_manual", quantidade_eletrodutos_sugestao
            )
            with col_sug:
                st.write(f"Sugestão: {quantidade_eletrodutos_sugestao}")
            with col_qtd_label:
                st.write("Quantidade:")
            with col_qtd_input:
                quantidade_input = st.text_input(
                    "Quantidade Eletrodutos",
                    value=st.session_state.get(
                        "quantidade_eletroduto_manual", quantidade_eletrodutos_sugestao
                    ),
                    key="quantidade_eletroduto_manual",
                    label_visibility="collapsed",
                )
            try:
                metragem_eletroduto = float(quantidade_input)
            except ValueError:
                metragem_eletroduto = 0.0
    
            total_infra_valor = preco_eletroduto * metragem_eletroduto
            with col_total:
                if total_infra_valor > 0:
                    st.write(f"Total: {format_currency(total_infra_valor)}")
                else:
                    st.write("Total:")
    
            st.markdown(
                """
                <style>
                div[data-testid=\"stTextInput\"] input[aria-label=\"Condulete sem rosca C-LL-LR-X\"] {
                    font-size: 24px;
                    font-weight: bold;
                    background-color: #ffffff;
                    color: #000000;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='font-size:24px; font-weight:bold;'>Condulete sem rosca C-LL-LR-X</p>",
                unsafe_allow_html=True,
            )
            st.text_input(
                "Condulete sem rosca C-LL-LR-X",
                value=st.session_state.get("custo_condulete", ""),
                key="custo_condulete",
                disabled=True,
                label_visibility="collapsed",
            )
    
            quantidade_conduletes = (
                math.ceil((soma_distancias / 3) * 1.5) if soma_distancias else 0
            )
            col_sug_c, col_qtd_label_c, col_qtd_input_c, col_total_c = st.columns(
                [1, 1, 2, 1]
            )
            quantidade_conduletes_sugestao = f"{quantidade_conduletes}"
            _definir_quantidade_padrao(
                "quantidade_condulete_manual", quantidade_conduletes_sugestao
            )
            with col_sug_c:
                st.write(f"Sugestão: {quantidade_conduletes_sugestao}")
            with col_qtd_label_c:
                st.write("Quantidade:")
            with col_qtd_input_c:
                quantidade_condulete_input = st.text_input(
                    "Quantidade Condulete",
                    value=st.session_state.get(
                        "quantidade_condulete_manual", quantidade_conduletes_sugestao
                    ),
                    key="quantidade_condulete_manual",
                    label_visibility="collapsed",
                )
            try:
                qtd_condulete = float(quantidade_condulete_input)
            except ValueError:
                qtd_condulete = 0.0
    
            total_condulete_valor = preco_condulete * qtd_condulete
            with col_total_c:
                if total_condulete_valor > 0:
                    st.write(f"Total: {format_currency(total_condulete_valor)}")
                else:
                    st.write("Total:")
    
            st.markdown(
                """
                <style>
                div[data-testid="stTextInput"] input[aria-label="Conduletes sem rosca T"] {
                    font-size: 24px;
                    font-weight: bold;
                    background-color: #ffffff;
                    color: #000000;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='font-size:24px; font-weight:bold;'>Conduletes sem rosca T</p>",
                unsafe_allow_html=True,
            )
            st.text_input(
                "Conduletes sem rosca T",
                value=st.session_state.get("custo_condulete_t", ""),
                key="custo_condulete_t",
                disabled=True,
                label_visibility="collapsed",
            )
    
            quantidade_conduletes_t = 1
            col_sug_t, col_qtd_label_t, col_qtd_input_t, col_total_t = st.columns(
                [1, 1, 2, 1]
            )
            quantidade_conduletes_t_sugestao = f"{quantidade_conduletes_t}"
            _definir_quantidade_padrao(
                "quantidade_condulete_t_manual", quantidade_conduletes_t_sugestao
            )
            with col_sug_t:
                st.write(f"Sugestão: {quantidade_conduletes_t_sugestao}")
            with col_qtd_label_t:
                st.write("Quantidade:")
            with col_qtd_input_t:
                quantidade_condulete_t_input = st.text_input(
                    "Quantidade Condulete T",
                    value=st.session_state.get(
                        "quantidade_condulete_t_manual",
                        quantidade_conduletes_t_sugestao,
                    ),
                    key="quantidade_condulete_t_manual",
                    label_visibility="collapsed",
                )
            try:
                qtd_condulete_t = float(quantidade_condulete_t_input)
            except ValueError:
                qtd_condulete_t = 0.0
    
            total_condulete_t_valor = preco_condulete_t * qtd_condulete_t
            with col_total_t:
                if total_condulete_t_valor > 0:
                    st.write(f"Total: {format_currency(total_condulete_t_valor)}")
                else:
                    st.write("Total:")
    
            st.markdown(
                """
                <style>
                div[data-testid=\"stTextInput\"] input[aria-label=\"Unidut Reto comum\"] {
                    font-size: 24px;
                    font-weight: bold;
                    background-color: #ffffff;
                    color: #000000;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='font-size:24px; font-weight:bold;'>Unidut Reto comum</p>",
                unsafe_allow_html=True,
            )
            st.text_input(
                "Unidut Reto comum",
                value=st.session_state.get("custo_unidut_reto", ""),
                key="custo_unidut_reto",
                disabled=True,
                label_visibility="collapsed",
            )
    
            quantidade_unidut_reto = (
                math.ceil((soma_distancias / 3) * 1.5) if soma_distancias else 0
            )
            col_sug_ur, col_qtd_label_ur, col_qtd_input_ur, col_total_ur = st.columns(
                [1, 1, 2, 1]
            )
            quantidade_unidut_reto_sugestao = f"{quantidade_unidut_reto}"
            _definir_quantidade_padrao(
                "quantidade_unidut_reto_manual", quantidade_unidut_reto_sugestao
            )
            with col_sug_ur:
                st.write(f"Sugestão: {quantidade_unidut_reto_sugestao}")
            with col_qtd_label_ur:
                st.write("Quantidade:")
            with col_qtd_input_ur:
                quantidade_unidut_reto_input = st.text_input(
                    "Quantidade Unidut Reto",
                    value=st.session_state.get(
                        "quantidade_unidut_reto_manual", quantidade_unidut_reto_sugestao
                    ),
                    key="quantidade_unidut_reto_manual",
                    label_visibility="collapsed",
                )
            try:
                qtd_unidut_reto = float(quantidade_unidut_reto_input)
            except ValueError:
                qtd_unidut_reto = 0.0
    
            total_unidut_reto_valor = preco_unidut_reto * qtd_unidut_reto
            with col_total_ur:
                if total_unidut_reto_valor > 0:
                    st.write(f"Total: {format_currency(total_unidut_reto_valor)}")
                else:
                    st.write("Total:")
    
            st.markdown(
                """
                <style>
                div[data-testid=\"stTextInput\"] input[aria-label=\"Unidut Cônico Comum\"] {
                    font-size: 24px;
                    font-weight: bold;
                    background-color: #ffffff;
                    color: #000000;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='font-size:24px; font-weight:bold;'>Unidut Cônico Comum</p>",
                unsafe_allow_html=True,
            )
            st.text_input(
                "Unidut Cônico Comum",
                value=st.session_state.get("custo_unidut_conico", ""),
                key="custo_unidut_conico",
                disabled=True,
                label_visibility="collapsed",
            )
    
            quantidade_unidut_conico = 3
            col_sug_uc, col_qtd_label_uc, col_qtd_input_uc, col_total_uc = st.columns(
                [1, 1, 2, 1]
            )
            quantidade_unidut_conico_sugestao = f"{quantidade_unidut_conico}"
            _definir_quantidade_padrao(
                "quantidade_unidut_conico_manual", quantidade_unidut_conico_sugestao
            )
            with col_sug_uc:
                st.write(f"Sugestão: {quantidade_unidut_conico_sugestao}")
            with col_qtd_label_uc:
                st.write("Quantidade:")
            with col_qtd_input_uc:
                quantidade_unidut_conico_input = st.text_input(
                    "Quantidade Unidut Cônico",
                    value=st.session_state.get(
                        "quantidade_unidut_conico_manual",
                        quantidade_unidut_conico_sugestao,
                    ),
                    key="quantidade_unidut_conico_manual",
                    label_visibility="collapsed",
                )
            try:
                qtd_unidut_conico = float(quantidade_unidut_conico_input)
            except ValueError:
                qtd_unidut_conico = 0.0
    
            total_unidut_conico_valor = preco_unidut_conico * qtd_unidut_conico
            with col_total_uc:
                if total_unidut_conico_valor > 0:
                    st.write(f"Total: {format_currency(total_unidut_conico_valor)}")
                else:
                    st.write("Total:")
    
            st.markdown(
                """
                <style>
                div[data-testid=\"stTextInput\"] input[aria-label=\"Curva Galv Eletro 90º\"] {
                    font-size: 24px;
                    font-weight: bold;
                    background-color: #ffffff;
                    color: #000000;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='font-size:24px; font-weight:bold;'>Curva Galv Eletro 90º</p>",
                unsafe_allow_html=True,
            )
            st.text_input(
                "Curva Galv Eletro 90º",
                value=st.session_state.get("custo_curva_galv_eletro_90", ""),
                key="custo_curva_galv_eletro_90",
                disabled=True,
                label_visibility="collapsed",
            )
    
            quantidade_curva = (
                math.ceil((soma_distancias / 3) * 1.2) if soma_distancias else 0
            )
            col_sug_curva, col_qtd_label_curva, col_qtd_input_curva, col_total_curva = st.columns(
                [1, 1, 2, 1]
            )
            quantidade_curva_sugestao = f"{quantidade_curva}"
            _definir_quantidade_padrao(
                "quantidade_curva_galv_eletro_90_manual", quantidade_curva_sugestao
            )
            with col_sug_curva:
                st.write(f"Sugestão: {quantidade_curva_sugestao}")
            with col_qtd_label_curva:
                st.write("Quantidade:")
            with col_qtd_input_curva:
                quantidade_curva_input = st.text_input(
                    "Quantidade Curva Galv Eletro 90º",
                    value=st.session_state.get(
                        "quantidade_curva_galv_eletro_90_manual",
                        quantidade_curva_sugestao,
                    ),
                    key="quantidade_curva_galv_eletro_90_manual",
                    label_visibility="collapsed",
                )
            try:
                qtd_curva = float(quantidade_curva_input)
            except ValueError:
                qtd_curva = 0.0
    
            total_curva_valor = preco_curva * qtd_curva
            with col_total_curva:
                if total_curva_valor > 0:
                    st.write(f"Total: {format_currency(total_curva_valor)}")
                else:
                    st.write("Total:")
    
            st.markdown(
                """
                <style>
                div[data-testid=\"stTextInput\"] input[aria-label=\"Unilet comum 90º\"] {
                    font-size: 24px;
                    font-weight: bold;
                    background-color: #ffffff;
                    color: #000000;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='font-size:24px; font-weight:bold;'>Unilet comum 90º</p>",
                unsafe_allow_html=True,
            )
            st.text_input(
                "Unilet comum 90º",
                value=st.session_state.get("custo_unilet", ""),
                key="custo_unilet",
                disabled=True,
                label_visibility="collapsed",
            )
    
            quantidade_unilet = 0
            col_sug_un, col_qtd_label_un, col_qtd_input_un, col_total_un = st.columns(
                [1, 1, 2, 1]
            )
            quantidade_unilet_sugestao = f"{quantidade_unilet}"
            _definir_quantidade_padrao(
                "quantidade_unilet_manual", quantidade_unilet_sugestao
            )
            with col_sug_un:
                st.write(f"Sugestão: {quantidade_unilet_sugestao}")
            with col_qtd_label_un:
                st.write("Quantidade:")
            with col_qtd_input_un:
                quantidade_unilet_input = st.text_input(
                    "Quantidade Unilet comum 90º",
                    value=st.session_state.get(
                        "quantidade_unilet_manual", quantidade_unilet_sugestao
                    ),
                    key="quantidade_unilet_manual",
                    label_visibility="collapsed",
                )
            try:
                qtd_unilet = float(quantidade_unilet_input)
            except ValueError:
                qtd_unilet = 0.0
    
            total_unilet_valor = preco_unilet * qtd_unilet
            with col_total_un:
                if total_unilet_valor > 0:
                    st.write(f"Total: {format_currency(total_unilet_valor)}")
                else:
                    st.write("Total:")
    
    
            st.markdown(
                """
                <style>
                div[data-testid="stTextInput"] input[aria-label="Abraçadeira D e Cunha"] {
                    font-size: 24px;
                    font-weight: bold;
                    background-color: #ffffff;
                    color: #000000;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='font-size:24px; font-weight:bold;'>Abraçadeira D e Cunha</p>",
                unsafe_allow_html=True,
            )
            st.text_input(
                "Abraçadeira D e Cunha",
                value=st.session_state.get("custo_abracadeira", ""),
                key="custo_abracadeira",
                disabled=True,
                label_visibility="collapsed",
            )
    
            quantidade_abracadeira = soma_distancias
            col_sug_ab, col_qtd_label_ab, col_qtd_input_ab, col_total_ab = st.columns([1, 1, 2, 1])
            quantidade_abracadeira_sugestao = f"{quantidade_abracadeira:g}"
            _definir_quantidade_padrao(
                "quantidade_abracadeira_manual", quantidade_abracadeira_sugestao
            )
            with col_sug_ab:
                st.write(f"Sugestão: {quantidade_abracadeira_sugestao}")
            with col_qtd_label_ab:
                st.write("Quantidade:")
            with col_qtd_input_ab:
                quantidade_abracadeira_input = st.text_input(
                    "Quantidade Abraçadeira D e Cunha",
                    value=st.session_state.get(
                        "quantidade_abracadeira_manual",
                        quantidade_abracadeira_sugestao,
                    ),
                    key="quantidade_abracadeira_manual",
                    label_visibility="collapsed",
                )
            try:
                qtd_abracadeira = float(quantidade_abracadeira_input)
            except ValueError:
                qtd_abracadeira = 0.0
    
            total_abracadeira_valor = preco_abracadeira * qtd_abracadeira
            with col_total_ab:
                if total_abracadeira_valor > 0:
                    st.write(f"Total: {format_currency(total_abracadeira_valor)}")
                else:
                    st.write("Total:")
            st.markdown(
                """
                <style>
                div[data-testid="stTextInput"] input[aria-label="Sealtubo com Capa"] {
                    font-size: 24px;
                    font-weight: bold;
                    background-color: #ffffff;
                    color: #000000;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='font-size:24px; font-weight:bold;'>Sealtubo com Capa</p>",
                unsafe_allow_html=True,
            )
            st.text_input(
                "Sealtubo com Capa",
                value=st.session_state.get("custo_sealtubo", ""),
                key="custo_sealtubo",
                disabled=True,
                label_visibility="collapsed",
            )
    
            quantidade_sealtubo = (
                soma_distancias / 20 if soma_distancias else 0.0
            )
            col_sug_seal, col_qtd_label_seal, col_qtd_input_seal, col_total_seal = st.columns(
                [1, 1, 2, 1]
            )
            quantidade_sealtubo_sugestao = f"{quantidade_sealtubo:.2f}"
            _definir_quantidade_padrao(
                "quantidade_sealtubo_manual", quantidade_sealtubo_sugestao
            )
            with col_sug_seal:
                st.write(f"Sugestão: {quantidade_sealtubo_sugestao}")
            with col_qtd_label_seal:
                st.write("Quantidade:")
            with col_qtd_input_seal:
                quantidade_sealtubo_input = st.text_input(
                    "Quantidade Sealtubo com Capa",
                    value=st.session_state.get(
                        "quantidade_sealtubo_manual", quantidade_sealtubo_sugestao
                    ),
                    key="quantidade_sealtubo_manual",
                    label_visibility="collapsed",
                )
            try:
                qtd_sealtubo = float(quantidade_sealtubo_input)
            except ValueError:
                qtd_sealtubo = 0.0
    
            total_sealtubo_valor = preco_sealtubo * qtd_sealtubo
            with col_total_seal:
                if total_sealtubo_valor > 0:
                    st.write(f"Total: {format_currency(total_sealtubo_valor)}")
                else:
                    st.write("Total:")
            total_infra_seca_valor = (
                total_infra_valor
                + total_condulete_valor
                + total_condulete_t_valor
                + total_unidut_reto_valor
                + total_unidut_conico_valor
                + total_curva_valor
                + total_unilet_valor
                + total_abracadeira_valor
                + total_sealtubo_valor
            )
            if total_infra_seca_valor > 0:
                st.write(
                    f"Total Infra-Seca: {format_currency(total_infra_seca_valor)}"
                )

            if st.session_state.get("deslocamento_necessario") == "Sim":
                custo_total = calcula_custo_deslocamento(
                    st.session_state.get("distancia_km", 0.0),
                    st.session_state.get("tempo_viagem", ""),
                    st.session_state.get("custo_pedagios", 0.0),
                    st.session_state["desloc_config"],
                )
                st.session_state["total_custo_deslocamento"] = custo_total
                st.success(
                    f"💰 Custo estimado de deslocamento: {format_currency(custo_total)}"
                )
            else:
                st.session_state["total_custo_deslocamento"] = 0.0
                st.info("Nenhum custo de deslocamento calculado.")

            st.markdown("---")
        with st.expander("🛡️ Quadro de Proteção", expanded=False):

            def _normalizar_texto(valor: str) -> str:
                if valor is None:
                    valor = ""
                valor = unicodedata.normalize("NFKD", str(valor))
                valor = "".join(ch for ch in valor if not unicodedata.combining(ch))
                valor = valor.lower()
                valor = re.sub(r"[^a-z0-9]+", " ", valor)
                return valor.strip()

            def _normalizar_chave(valor: str, indice: int) -> str:
                base = re.sub(r"[^0-9a-zA-Z]+", "_", valor).strip("_").lower()
                return f"{base}_{indice}" if base else f"item_{indice}"

            def _obter_sugestao_quantidade(descricao: str) -> float:
                if not descricao:
                    return 1.0
                match = re.match(r"\s*(\d+(?:[.,]\d+)?)\s*[xX]", descricao)
                if match:
                    try:
                        return float(match.group(1).replace(",", "."))
                    except ValueError:
                        return 1.0
                return 1.0

            df_disjuntores_din_preco = _load_editor_dataframe(
                "valores_disjuntores_din_df"
            )
            if df_disjuntores_din_preco is None or df_disjuntores_din_preco.empty:
                try:
                    df_disjuntores_din_preco = pd.read_csv(
                        "valores_disjuntor_din.csv", sep=";"
                    )
                except FileNotFoundError:
                    df_disjuntores_din_preco = pd.DataFrame()
            else:
                df_disjuntores_din_preco = df_disjuntores_din_preco.copy()

            if not df_disjuntores_din_preco.empty:
                if "Material" in df_disjuntores_din_preco.columns:
                    df_disjuntores_din_preco["Material"] = (
                        df_disjuntores_din_preco["Material"].astype(str)
                    )
                if "Preco" in df_disjuntores_din_preco.columns:
                    df_disjuntores_din_preco["_PrecoNumerico"] = (
                        df_disjuntores_din_preco["Preco"].apply(_parse_float_field)
                    )
                else:
                    df_disjuntores_din_preco["_PrecoNumerico"] = 0.0
            else:
                df_disjuntores_din_preco = pd.DataFrame(
                    columns=["Material", "Preco", "_PrecoNumerico"]
                )

            df_idr_preco = _load_editor_dataframe("valores_idr_df")
            if df_idr_preco is None or df_idr_preco.empty:
                try:
                    df_idr_preco = pd.read_csv("valores_idr.csv", sep=";")
                except FileNotFoundError:
                    df_idr_preco = pd.DataFrame(
                        columns=[
                            "Material",
                            "Preco",
                            "Atualizado",
                            "_PrecoNumerico",
                            "_Polos",
                            "_Corrente",
                            "_Sensibilidade",
                        ]
                    )
            else:
                df_idr_preco = df_idr_preco.copy()

            if not df_idr_preco.empty:
                if "Material" in df_idr_preco.columns:
                    df_idr_preco["Material"] = df_idr_preco["Material"].astype(str)
                else:
                    df_idr_preco["Material"] = ""
                if "Preco" in df_idr_preco.columns:
                    df_idr_preco["_PrecoNumerico"] = df_idr_preco["Preco"].apply(
                        _parse_float_field
                    )
                else:
                    df_idr_preco["_PrecoNumerico"] = 0.0
                df_idr_preco["_Polos"] = (
                    df_idr_preco["Material"]
                    .str.extract(r"(\dP)", expand=False)
                    .str.upper()
                    .fillna("")
                )
                df_idr_preco["_Corrente"] = pd.to_numeric(
                    df_idr_preco["Material"]
                    .str.extract(r"(\d+(?:[.,]\d+)?)(?:\s*)A", expand=False)
                    .str.replace(",", ".", regex=False),
                    errors="coerce",
                )
                df_idr_preco["_Sensibilidade"] = pd.to_numeric(
                    df_idr_preco["Material"]
                    .str.extract(r"(\d+)(?:\s*)mA", expand=False),
                    errors="coerce",
                )
            else:
                df_idr_preco = pd.DataFrame(
                    columns=[
                        "Material",
                        "Preco",
                        "_PrecoNumerico",
                        "_Polos",
                        "_Corrente",
                        "_Sensibilidade",
                    ]
                )

            df_dps_preco = _load_editor_dataframe("valores_dps_df")
            if df_dps_preco is None or df_dps_preco.empty:
                try:
                    df_dps_preco = pd.read_csv("valores_dps.csv", sep=";")
                except FileNotFoundError:
                    df_dps_preco = pd.DataFrame(
                        columns=[
                            "Material",
                            "Preco",
                            "Atualizado",
                            "_PrecoNumerico",
                            "_Ka",
                            "_Tipo",
                        ]
                    )
            else:
                df_dps_preco = df_dps_preco.copy()

            if not df_dps_preco.empty:
                if "Material" in df_dps_preco.columns:
                    df_dps_preco["Material"] = df_dps_preco["Material"].astype(str)
                else:
                    df_dps_preco["Material"] = ""
                if "Preco" in df_dps_preco.columns:
                    df_dps_preco["_PrecoNumerico"] = df_dps_preco["Preco"].apply(
                        _parse_float_field
                    )
                else:
                    df_dps_preco["_PrecoNumerico"] = 0.0
                df_dps_preco["_Ka"] = pd.to_numeric(
                    df_dps_preco["Material"]
                    .str.extract(r"(\d+(?:[.,]\d+)?)\s*kA", expand=False)
                    .str.replace(",", ".", regex=False),
                    errors="coerce",
                )
                df_dps_preco["_Tipo"] = pd.to_numeric(
                    df_dps_preco["Material"].str.extract(r"tipo\s*(\d+)", expand=False),
                    errors="coerce",
                )
            else:
                df_dps_preco = pd.DataFrame(
                    columns=["Material", "Preco", "_PrecoNumerico", "_Ka", "_Tipo"]
                )

            df_barra_pente_preco = _load_editor_dataframe("valores_barra_pente_df")
            if df_barra_pente_preco is None or df_barra_pente_preco.empty:
                try:
                    df_barra_pente_preco = pd.read_csv("valores_barra_pente.csv", sep=";")
                except FileNotFoundError:
                    df_barra_pente_preco = pd.DataFrame(
                        columns=[
                            "Material",
                            "Preco",
                            "Atualizado",
                            "_PrecoNumerico",
                            "_MaterialNormalizado",
                        ]
                    )
            else:
                df_barra_pente_preco = df_barra_pente_preco.copy()

            if not df_barra_pente_preco.empty:
                if "Material" in df_barra_pente_preco.columns:
                    df_barra_pente_preco["Material"] = (
                        df_barra_pente_preco["Material"].astype(str)
                    )
                else:
                    df_barra_pente_preco["Material"] = ""
                if "Preco" in df_barra_pente_preco.columns:
                    df_barra_pente_preco["_PrecoNumerico"] = (
                        df_barra_pente_preco["Preco"].apply(_parse_float_field)
                    )
                else:
                    df_barra_pente_preco["_PrecoNumerico"] = 0.0
                df_barra_pente_preco["_MaterialNormalizado"] = (
                    df_barra_pente_preco["Material"].apply(_normalizar_texto)
                )
            else:
                df_barra_pente_preco = pd.DataFrame(
                    columns=[
                        "Material",
                        "Preco",
                        "_PrecoNumerico",
                        "_MaterialNormalizado",
                    ]
                )

            df_paineis_quadros_preco = _load_editor_dataframe("valores_paineis_quadros_df")
            if df_paineis_quadros_preco is None or df_paineis_quadros_preco.empty:
                try:
                    df_paineis_quadros_preco = pd.read_csv(
                        "valores_paineis_quadros.csv", sep=";"
                    )
                except FileNotFoundError:
                    df_paineis_quadros_preco = pd.DataFrame(
                        columns=[
                            "Material",
                            "Preco",
                            "Atualizado",
                            "_PrecoNumerico",
                            "_MaterialNormalizado",
                        ]
                    )
            else:
                df_paineis_quadros_preco = df_paineis_quadros_preco.copy()

            if not df_paineis_quadros_preco.empty:
                if "Material" in df_paineis_quadros_preco.columns:
                    df_paineis_quadros_preco["Material"] = (
                        df_paineis_quadros_preco["Material"].astype(str)
                    )
                else:
                    df_paineis_quadros_preco["Material"] = ""
                df_paineis_quadros_preco["Material"] = df_paineis_quadros_preco[
                    "Material"
                ].str.replace("×", "x", regex=False)
                if "Preco" in df_paineis_quadros_preco.columns:
                    df_paineis_quadros_preco["_PrecoNumerico"] = (
                        df_paineis_quadros_preco["Preco"].apply(_parse_float_field)
                    )
                else:
                    df_paineis_quadros_preco["_PrecoNumerico"] = 0.0
                df_paineis_quadros_preco["_MaterialNormalizado"] = (
                    df_paineis_quadros_preco["Material"].apply(_normalizar_texto)
                )
            else:
                df_paineis_quadros_preco = pd.DataFrame(
                    columns=[
                        "Material",
                        "Preco",
                        "_PrecoNumerico",
                        "_MaterialNormalizado",
                    ]
                )

            def _obter_preco_disjuntor(descricao: str) -> float:
                """Retorna o preço do disjuntor com base na tabela de atualização."""
                if not descricao:
                    return 0.0
                if df_disjuntores_din_preco.empty:
                    return 0.0

                match = re.search(r"(1P\+N|\dP)\s*(\d+(?:[.,]\d+)?)\s*A", descricao, re.IGNORECASE)
                if not match:
                    return 0.0

                polos = match.group(1).upper()
                corrente_txt = match.group(2).replace(",", ".")
                try:
                    corrente = int(round(float(corrente_txt)))
                except ValueError:
                    return 0.0

                polos_busca = "2P" if polos == "1P+N" else polos

                material_mask = (
                    df_disjuntores_din_preco["Material"].str.contains(
                        polos_busca, case=False, na=False
                    )
                    & df_disjuntores_din_preco["Material"].str.contains(
                        f"{corrente}A", case=False, na=False
                    )
                )
                linha_correspondente = df_disjuntores_din_preco.loc[material_mask]
                if linha_correspondente.empty:
                    return 0.0

                preco = linha_correspondente.iloc[0]["_PrecoNumerico"]
                if pd.isna(preco):
                    return 0.0
                return float(preco)

            def _obter_preco_idr(descricao: str) -> float:
                """Retorna o preço do IDR correspondente à descrição informada."""
                if not descricao or df_idr_preco.empty:
                    return 0.0

                polos_match = re.search(r"(\dP)", descricao, re.IGNORECASE)
                corrente_match = re.search(
                    r"(\d+(?:[.,]\d+)?)(?:\s*)A", descricao, re.IGNORECASE
                )
                sensibilidade_match = re.search(
                    r"(\d+)(?:\s*)mA", descricao, re.IGNORECASE
                )

                if not polos_match or not corrente_match:
                    return 0.0

                polos = polos_match.group(1).upper()
                try:
                    corrente = int(round(float(corrente_match.group(1).replace(",", "."))))
                except ValueError:
                    return 0.0

                sensibilidade = None
                if sensibilidade_match:
                    try:
                        sensibilidade = int(sensibilidade_match.group(1))
                    except ValueError:
                        sensibilidade = None

                for _, linha in df_idr_preco.iterrows():
                    if str(linha.get("_Polos", "")).upper() != polos:
                        continue
                    corrente_linha = linha.get("_Corrente")
                    if pd.isna(corrente_linha):
                        continue
                    try:
                        corrente_linha = int(round(float(corrente_linha)))
                    except (TypeError, ValueError):
                        continue
                    if corrente_linha != corrente:
                        continue

                    sensibilidade_linha = linha.get("_Sensibilidade")
                    if sensibilidade is not None and not pd.isna(sensibilidade_linha):
                        try:
                            sensibilidade_linha = int(round(float(sensibilidade_linha)))
                        except (TypeError, ValueError):
                            sensibilidade_linha = None
                        if (
                            sensibilidade_linha is not None
                            and sensibilidade_linha != sensibilidade
                        ):
                            continue

                    preco = linha.get("_PrecoNumerico")
                    if pd.isna(preco):
                        continue
                    return float(preco)

                return 0.0

            def _obter_preco_dps(descricao: str) -> float:
                """Retorna o preço do DPS correspondente à descrição informada."""
                if not descricao or df_dps_preco.empty:
                    return 0.0

                ka_match = re.search(r"(\d+(?:[.,]\d+)?)\s*kA", descricao, re.IGNORECASE)
                tipo_match = re.search(r"tipo\s*(\d+)", descricao, re.IGNORECASE)

                ka_val = None
                if ka_match:
                    try:
                        ka_val = float(ka_match.group(1).replace(",", "."))
                    except ValueError:
                        ka_val = None

                tipo_val = None
                if tipo_match:
                    try:
                        tipo_val = float(tipo_match.group(1))
                    except ValueError:
                        tipo_val = None

                if ka_val is None and tipo_val is None:
                    return 0.0

                mask = pd.Series(True, index=df_dps_preco.index, dtype=bool)
                if ka_val is not None and "_Ka" in df_dps_preco.columns:
                    mask &= df_dps_preco["_Ka"].round().fillna(-1.0) == ka_val
                if tipo_val is not None and "_Tipo" in df_dps_preco.columns:
                    mask &= df_dps_preco["_Tipo"].round().fillna(-1.0) == tipo_val

                linha_correspondente = df_dps_preco.loc[mask]

                if linha_correspondente.empty:
                    texto_busca = df_dps_preco["Material"].astype(str).str.lower()
                    mask = pd.Series(True, index=df_dps_preco.index, dtype=bool)
                    if ka_val is not None:
                        mask &= texto_busca.str.contains(
                            rf"{ka_val:g}\s*kA", case=False, na=False, regex=True
                        )
                    if tipo_val is not None:
                        mask &= texto_busca.str.contains(
                            rf"tipo\s*{tipo_val:g}", case=False, na=False, regex=True
                        )
                    linha_correspondente = df_dps_preco.loc[mask]

                if linha_correspondente.empty:
                    return 0.0

                preco = linha_correspondente.iloc[0].get("_PrecoNumerico")
                if pd.isna(preco):
                    return 0.0
                return float(preco)

            def _obter_preco_quadro(
                descricao: str, titulo_componente: str
            ) -> float:
                """Retorna o preço do quadro ou painel informado."""
                if not descricao or df_paineis_quadros_preco.empty:
                    return 0.0

                descricao = str(descricao).replace("×", "x")
                desc_norm = _normalizar_texto(descricao)
                if not desc_norm:
                    return 0.0

                candidatos = df_paineis_quadros_preco.copy()
                titulo_norm = _normalizar_texto(titulo_componente)

                if "pvc" in titulo_norm:
                    candidatos = candidatos[
                        candidatos["_MaterialNormalizado"].str.contains(
                            "pvc", na=False
                        )
                    ]
                elif "metal" in titulo_norm:
                    candidatos = candidatos[
                        candidatos["_MaterialNormalizado"].str.contains(
                            "metal", na=False
                        )
                    ]

                numeros = re.findall(r"\d+", desc_norm)
                for numero in numeros:
                    if candidatos.empty:
                        break
                    candidatos = candidatos[
                        candidatos["_MaterialNormalizado"].str.contains(
                            numero, na=False
                        )
                    ]

                if candidatos.empty:
                    tokens = [
                        token
                        for token in desc_norm.split()
                        if token not in {"quadro", "de", "posicoes", "posicao"}
                    ]
                    melhor_preco = 0.0
                    melhor_score = 0
                    for _, linha in df_paineis_quadros_preco.iterrows():
                        material_norm = str(
                            linha.get("_MaterialNormalizado", "")
                        )
                        if not material_norm:
                            continue
                        score = sum(1 for token in tokens if token in material_norm)
                        if score > melhor_score and not pd.isna(
                            linha.get("_PrecoNumerico")
                        ):
                            melhor_score = score
                            melhor_preco = float(linha["_PrecoNumerico"])
                    return melhor_preco

                preco = candidatos.iloc[0].get("_PrecoNumerico")
                if pd.isna(preco):
                    return 0.0
                return float(preco)

            def _obter_preco_barra_pente(descricao: str, dps_descricao: str) -> float:
                """Retorna o preço da barra pente associado ao DPS informado."""
                if df_barra_pente_preco.empty:
                    return 0.0

                descricao_norm = _normalizar_texto(descricao)
                dps_norm = _normalizar_texto(dps_descricao)
                instalacao_norm = _normalizar_texto(
                    st.session_state.get("instalacao_sistema", "")
                )

                chaves_busca = []
                if re.search(r"\btri", descricao_norm) or "tripolar" in descricao_norm:
                    chaves_busca.append("tri")
                if re.search(r"\bbip?", descricao_norm) or "bipolar" in descricao_norm:
                    chaves_busca.append("bif")
                if "monopolar" in descricao_norm or "mono" in descricao_norm:
                    chaves_busca.append("mono")

                if not chaves_busca and dps_norm:
                    quantidade_match = re.search(r"(\d+)x", dps_norm)
                    if quantidade_match:
                        try:
                            quantidade = int(quantidade_match.group(1))
                            if quantidade >= 3:
                                chaves_busca.append("tri")
                            else:
                                chaves_busca.append("bif")
                        except ValueError:
                            pass

                if not chaves_busca and instalacao_norm:
                    if "tri" in instalacao_norm:
                        chaves_busca.append("tri")
                    elif "bi" in instalacao_norm or "bif" in instalacao_norm:
                        chaves_busca.append("bif")
                    elif "mono" in instalacao_norm:
                        chaves_busca.append("mono")

                if not chaves_busca:
                    chaves_busca = ["bif", "tri", "mono"]

                chaves_busca = list(dict.fromkeys(chaves_busca))

                for chave in chaves_busca:
                    mask = df_barra_pente_preco["_MaterialNormalizado"].str.contains(
                        chave, na=False
                    )
                    linha_correspondente = df_barra_pente_preco.loc[mask]
                    if not linha_correspondente.empty:
                        preco = linha_correspondente.iloc[0].get("_PrecoNumerico")
                        if not pd.isna(preco):
                            return float(preco)

                preco_fallback = df_barra_pente_preco.iloc[0].get("_PrecoNumerico")
                if pd.isna(preco_fallback):
                    return 0.0
                return float(preco_fallback)

            def _render_mini_disjuntor_inputs() -> None:
                st.markdown("**Mini-Disjuntor Adicional**")
                st.checkbox(
                    "Mini-Disjuntor Adicional",
                    key="mini_disjuntor_adicional",
                )
                if st.session_state.get("mini_disjuntor_adicional"):
                    disjuntores_din_opcoes = []
                    if not df_disjuntores_din_preco.empty:
                        disjuntores_din_opcoes = (
                            df_disjuntores_din_preco["Material"]
                            .dropna()
                            .astype(str)
                            .tolist()
                        )
                    if not disjuntores_din_opcoes:
                        disjuntores_din_opcoes = ["Disjuntor DIN"]
                    mini_disjuntor_tipo = st.selectbox(
                        "Tipo do Mini-Disjuntor Adicional",
                        options=disjuntores_din_opcoes,
                        key="mini_disjuntor_adicional_tipo",
                    )
                    preco_key = "mini_disjuntor_preco_unitario"
                    preco_ref_key = "mini_disjuntor_preco_unitario_ref"
                    preco_padrao = _obter_preco_disjuntor(mini_disjuntor_tipo)
                    if preco_padrao > 0:
                        preco_padrao_texto = format_currency(preco_padrao)
                        ref_anterior = st.session_state.get(preco_ref_key)
                        if ref_anterior != mini_disjuntor_tipo:
                            st.session_state[preco_key] = preco_padrao_texto
                            st.session_state[preco_ref_key] = mini_disjuntor_tipo
                    preco_valor = float(preco_padrao) if preco_padrao > 0 else 0.0
                    quantidade_valor = 1.0
                    st.session_state[preco_key] = (
                        format_currency(preco_valor) if preco_valor > 0 else ""
                    )
                    st.session_state["mini_disjuntor_quantidade"] = "1"
                    total_item = preco_valor * quantidade_valor
                    st.session_state["mini_disjuntor_preco_valor"] = preco_valor
                    st.session_state["mini_disjuntor_quantidade_valor"] = quantidade_valor
                    st.session_state["total_mini_disjuntor_adicional"] = total_item
                else:
                    st.session_state["mini_disjuntor_preco_valor"] = 0.0
                    st.session_state["mini_disjuntor_quantidade_valor"] = 0.0
                    st.session_state["total_mini_disjuntor_adicional"] = 0.0

            mini_disjuntor_adicional = st.session_state.get(
                "mini_disjuntor_adicional", False
            )
            mini_disjuntor_tipo = st.session_state.get("mini_disjuntor_adicional_tipo")
            if mini_disjuntor_adicional and not mini_disjuntor_tipo:
                if not df_disjuntores_din_preco.empty:
                    mini_disjuntor_tipo = (
                        df_disjuntores_din_preco["Material"]
                        .dropna()
                        .astype(str)
                        .iloc[0]
                    )
                else:
                    mini_disjuntor_tipo = "Disjuntor DIN"

            quadro_componentes = []
            disjuntor_val = st.session_state.get("disjuntor_recomendado", "")
            if disjuntor_val:
                quadro_componentes.append(("Disjuntor", disjuntor_val))
            if mini_disjuntor_adicional:
                mini_disjuntor_val = mini_disjuntor_tipo
                if mini_disjuntor_val:
                    quadro_componentes.append(
                        ("Mini-Disjuntor Adicional", mini_disjuntor_val)
                    )
                else:
                    st.info(
                        "Selecione um disjuntor DIN para usar como mini-disjuntor adicional."
                    )
            idr_val = st.session_state.get("idr_recomendado", "")
            if idr_val:
                quadro_componentes.append(("IDR (Interruptor Diferencial Residual)", idr_val))
            dps_val = st.session_state.get("dps_recomendado", "")
            if dps_val:
                quadro_componentes.append(("DPS (Dispositivo de Proteção contra Surtos)", dps_val))
            barra_pente_val = st.session_state.get("barra_pente_recomendado", "")
            if barra_pente_val:
                quadro_componentes.append(("Barra Pente", barra_pente_val))
            quadro_pvc_val = st.session_state.get("quadro_pvc_recomendado", "")
            quadro_metalico_val = st.session_state.get("quadro_metalico_recomendado", "")
            if quadro_pvc_val:
                quadro_componentes.append(("Quadro PVC", quadro_pvc_val))
            elif quadro_metalico_val:
                quadro_componentes.append(("Quadro Metálico", quadro_metalico_val))

            total_quadro_protecao_valor = 0.0
            total_mini_quadro_valor = 0.0
            quadro_dados = []

            mini_disjuntor_rendered = False
            tipo_servico_atual = (
                st.session_state.get("tipo_servico", "")
                or st.session_state.get("tipo_servico_orcamento", "")
            )
            if not quadro_componentes:
                _render_mini_disjuntor_inputs()
                st.info("Nenhum componente de quadro de proteção disponível no momento.")
            else:
                for indice, (titulo_componente, descricao) in enumerate(quadro_componentes):
                    chave_item = _normalizar_chave(titulo_componente, indice)
                    sugestao = _obter_sugestao_quantidade(descricao)
                    if titulo_componente == "Disjuntor":
                        sugestao = 2.0
                    if (
                        tipo_servico_atual in {"Análise de Energia", "Manutenção Corretiva"}
                        and titulo_componente in {"Barra Pente", "Quadro PVC"}
                    ):
                        sugestao = 0.0
                    st.markdown(
                        f"""
                        <style>
                        div[data-testid=\"stTextInput\"] input[aria-label=\"{titulo_componente}\"] {{
                            font-size: 24px;
                            font-weight: bold;
                            background-color: #ffffff;
                            color: #000000;
                        }}
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<p style='font-size:24px; font-weight:bold;'>{titulo_componente}</p>",
                        unsafe_allow_html=True,
                    )
                    st.text_input(
                        titulo_componente,
                        value=descricao,
                        key=f"quadro_protecao_{chave_item}",
                        disabled=True,
                        label_visibility="collapsed",
                    )

                    col_sug, col_preco, col_qtd, col_total = st.columns([1, 1, 1, 1])
                    sugestao_float = float(sugestao)
                    if sugestao_float.is_integer():
                        sugestao_texto = str(int(sugestao_float))
                    else:
                        sugestao_texto = f"{sugestao_float:.2f}"
                    with col_sug:
                        st.write(f"Sugestão: {sugestao_texto}")
                    with col_preco:
                        st.write("Preço unitário:")
                        preco_padrao = 0.0
                        preco_padrao_texto = ""
                        preco_key = f"preco_quadro_{chave_item}"
                        preco_ref_key = f"{preco_key}_ref"
                        if titulo_componente == "Disjuntor":
                            preco_padrao = _obter_preco_disjuntor(descricao)
                            if preco_padrao > 0:
                                preco_padrao_texto = format_currency(preco_padrao)
                                ref_anterior = st.session_state.get(preco_ref_key)
                                if ref_anterior != descricao:
                                    st.session_state[preco_key] = preco_padrao_texto
                                    st.session_state[preco_ref_key] = descricao
                        elif titulo_componente == "Mini-Disjuntor Adicional":
                            preco_padrao = _obter_preco_disjuntor(descricao)
                            if preco_padrao > 0:
                                preco_padrao_texto = format_currency(preco_padrao)
                                ref_anterior = st.session_state.get(preco_ref_key)
                                if ref_anterior != descricao:
                                    st.session_state[preco_key] = preco_padrao_texto
                                    st.session_state[preco_ref_key] = descricao
                        elif (
                            titulo_componente
                            == "IDR (Interruptor Diferencial Residual)"
                        ):
                            preco_padrao = _obter_preco_idr(descricao)
                            if preco_padrao > 0:
                                preco_padrao_texto = format_currency(preco_padrao)
                                ref_anterior = st.session_state.get(preco_ref_key)
                                if ref_anterior != descricao:
                                    st.session_state[preco_key] = preco_padrao_texto
                                    st.session_state[preco_ref_key] = descricao
                        elif (
                            titulo_componente
                            == "DPS (Dispositivo de Proteção contra Surtos)"
                        ):
                            preco_padrao = _obter_preco_dps(descricao)
                            if preco_padrao > 0:
                                preco_padrao_texto = format_currency(preco_padrao)
                                ref_anterior = st.session_state.get(preco_ref_key)
                                if ref_anterior != descricao:
                                    st.session_state[preco_key] = preco_padrao_texto
                                    st.session_state[preco_ref_key] = descricao
                        elif titulo_componente == "Barra Pente":
                            preco_padrao = _obter_preco_barra_pente(descricao, dps_val)
                            if preco_padrao > 0:
                                preco_padrao_texto = format_currency(preco_padrao)
                                ref_anterior = st.session_state.get(preco_ref_key)
                                if ref_anterior != descricao:
                                    st.session_state[preco_key] = preco_padrao_texto
                                    st.session_state[preco_ref_key] = descricao
                        elif titulo_componente in {"Quadro PVC", "Quadro Metálico"}:
                            preco_padrao = _obter_preco_quadro(
                                descricao, titulo_componente
                            )
                            if preco_padrao > 0:
                                preco_padrao_texto = format_currency(preco_padrao)
                                ref_anterior = st.session_state.get(preco_ref_key)
                                if ref_anterior != descricao:
                                    st.session_state[preco_key] = preco_padrao_texto
                                    st.session_state[preco_ref_key] = descricao
                        preco_input = st.text_input(
                            f"Preço {titulo_componente}",
                            value=preco_padrao_texto,
                            key=f"preco_quadro_{chave_item}",
                            label_visibility="collapsed",
                            placeholder="R$ 0,00",
                        )
                        preco_valor = _parse_float_field(preco_input)
                    with col_qtd:
                        st.write("Quantidade:")
                        if (
                            tipo_servico_atual in {"Análise de Energia", "Manutenção Corretiva"}
                            and titulo_componente in {"Barra Pente", "Quadro PVC"}
                        ):
                            st.session_state[f"quantidade_quadro_{chave_item}"] = "0"
                        quantidade_input = st.text_input(
                            f"Quantidade {titulo_componente}",
                            value=sugestao_texto,
                            key=f"quantidade_quadro_{chave_item}",
                            label_visibility="collapsed",
                        )
                        quantidade_valor = _parse_float_field(quantidade_input)
                    total_item = preco_valor * quantidade_valor
                    with col_total:
                        if total_item > 0:
                            st.write(f"Total: {format_currency(total_item)}")
                        else:
                            st.write("Total:")

                    if total_item > 0:
                        total_quadro_protecao_valor += total_item
                        if titulo_componente == "Mini-Disjuntor Adicional":
                            total_mini_quadro_valor = total_item
                        quadro_dados.append(
                            {
                                "Item": descricao or titulo_componente,
                                "Bitola (mm²)": "",
                                "Valor Unitário": format_currency(preco_valor),
                                "Quantidade (m)": f"{quantidade_valor:.2f}",
                                "Total": format_currency(total_item),
                            }
                        )
                    if titulo_componente == "Disjuntor":
                        _render_mini_disjuntor_inputs()
                        mini_disjuntor_rendered = True

                if not mini_disjuntor_rendered:
                    _render_mini_disjuntor_inputs()

            total_mini_disjuntor_adicional = st.session_state.get(
                "total_mini_disjuntor_adicional", 0.0
            )
            if total_mini_disjuntor_adicional > 0 and total_mini_quadro_valor == 0:
                total_quadro_protecao_valor += total_mini_disjuntor_adicional
                quadro_dados.append(
                    {
                        "Item": mini_disjuntor_tipo or "Mini-Disjuntor Adicional",
                        "Bitola (mm²)": "",
                        "Valor Unitário": format_currency(
                            st.session_state.get("mini_disjuntor_preco_valor", 0.0)
                        ),
                        "Quantidade (m)": f"{st.session_state.get('mini_disjuntor_quantidade_valor', 0.0):.2f}",
                        "Total": format_currency(total_mini_disjuntor_adicional),
                    }
                )

            if total_quadro_protecao_valor > 0:
                st.write(
                    f"Total Quadro de Proteção: {format_currency(total_quadro_protecao_valor)}"
                )
            st.session_state["total_quadro_protecao"] = total_quadro_protecao_valor

        total_material_adicional_valor = 0.0
        material_adicional_dados = []
        material_adicional_flags = (
            "disjuntor_caixa_moldada",
            "barra_roscada",
            "eletrocalha",
            "tem_tomada_industrial",
            "tem_medidor",
            "transformador",
            "totem",
        )
        mostrar_material_adicional = any(
            st.session_state.get(chave) == "Sim"
            for chave in material_adicional_flags
        )

        if mostrar_material_adicional:
            with st.expander("📦 Material Adicional", expanded=False):
                if st.session_state.get("disjuntor_caixa_moldada") == "Sim":
                    st.markdown("**Disjuntor Caixa Moldada**")
                    disjuntor_fallback = [
                        {
                            "Modelo": "440V EZC100N3100",
                            "Corrente": "100A",
                            "Fabricante": "Schneider",
                            "Preco": 361.99,
                        },
                        {
                            "Modelo": "690VCA 3KA SDJS125",
                            "Corrente": "125A",
                            "Fabricante": "Steck",
                            "Preco": 368.99,
                        },
                        {
                            "Modelo": "DWP250 20KA",
                            "Corrente": "150A",
                            "Fabricante": "WEG",
                            "Preco": 434.90,
                        },
                        {
                            "Modelo": "400V20KA DWP250L1603",
                            "Corrente": "160A",
                            "Fabricante": "WEG",
                            "Preco": 435.49,
                        },
                        {
                            "Modelo": "690VCA 3KA SDJS200",
                            "Corrente": "200A",
                            "Fabricante": "Steck",
                            "Preco": 444.99,
                        },
                        {
                            "Modelo": "Asgard",
                            "Corrente": "250A",
                            "Fabricante": "Steck",
                            "Preco": 512.54,
                        },
                        {
                            "Modelo": "690VCA 10KA SDJS300",
                            "Corrente": "300A",
                            "Fabricante": "Steck",
                            "Preco": 891.78,
                        },
                        {
                            "Modelo": "690V 10KA",
                            "Corrente": "350A",
                            "Fabricante": "Steck",
                            "Preco": 1106.99,
                        },
                        {
                            "Modelo": "690Vac/250Vdc 70KA SDJS400",
                            "Corrente": "400A",
                            "Fabricante": "Steck",
                            "Preco": 1070.99,
                        },
                        {
                            "Modelo": "Asgard",
                            "Corrente": "450A",
                            "Fabricante": "Steck",
                            "Preco": 2700.71,
                        },
                        {
                            "Modelo": "Asgard",
                            "Corrente": "500A",
                            "Fabricante": "Steck",
                            "Preco": 2707.18,
                        },
                        {
                            "Modelo": "Asgard",
                            "Corrente": "600A",
                            "Fabricante": "Steck",
                            "Preco": 2707.18,
                        },
                    ]
                    df_disjuntores = _load_price_table(
                        "valores_disjuntores_df",
                        "valores_disjuntores_editor",
                        "valores_disjuntor_caixa_moldada.csv",
                        disjuntor_fallback,
                    )
                    opcoes_disjuntores = [""]
                    if not df_disjuntores.empty and "Modelo" in df_disjuntores.columns:
                        opcoes_disjuntores.extend(
                            [
                                str(modelo)
                                for modelo in df_disjuntores["Modelo"]
                                .dropna()
                                .astype(str)
                                .unique()
                            ]
                        )
                    selectbox_key = "custos_modelo_disjuntor_caixa_moldada"
                    _sync_selectbox_state(
                        selectbox_key,
                        "modelo_disjuntor_caixa_moldada",
                        opcoes_disjuntores,
                    )
                    col_item, col_preco, col_qtd, col_total = st.columns([3, 2, 1, 1])
                    with col_item:
                        modelo_disjuntor = st.selectbox(
                            "Modelo",
                            opcoes_disjuntores,
                            key=selectbox_key,
                        )
                        st.session_state[
                            "modelo_disjuntor_caixa_moldada"
                        ] = modelo_disjuntor
                        info_partes = []
                        if (
                            modelo_disjuntor
                            and not df_disjuntores.empty
                            and "Modelo" in df_disjuntores.columns
                        ):
                            linha_dj = df_disjuntores[
                                df_disjuntores["Modelo"].astype(str) == modelo_disjuntor
                            ]
                            if not linha_dj.empty:
                                corrente = str(linha_dj.iloc[0].get("Corrente", "")).strip()
                                fabricante = (
                                    str(linha_dj.iloc[0].get("Fabricante", "")).strip()
                                )
                                if corrente:
                                    info_partes.append(corrente)
                                if fabricante:
                                    info_partes.append(fabricante)
                        if info_partes:
                            st.caption(" • ".join(info_partes))
                    preco_key_dj = "custos_preco_disjuntor_caixa_moldada"
                    preco_ref_key_dj = "custos_preco_disjuntor_caixa_moldada_ref"
                    quantidade_key_dj = "custos_quantidade_disjuntor_caixa_moldada"
                    preco_padrao_dj = 0.0
                    if (
                        modelo_disjuntor
                        and not df_disjuntores.empty
                        and "Modelo" in df_disjuntores.columns
                    ):
                        linha_dj = df_disjuntores[
                            df_disjuntores["Modelo"].astype(str) == modelo_disjuntor
                        ]
                        if not linha_dj.empty:
                            preco_padrao_dj = float(linha_dj.iloc[0]["_PrecoNumerico"])
                    preco_padrao_texto_dj = (
                        format_currency(preco_padrao_dj) if preco_padrao_dj > 0 else ""
                    )
                    if preco_key_dj not in st.session_state:
                        st.session_state[preco_key_dj] = preco_padrao_texto_dj
                    if (
                        preco_padrao_texto_dj
                        and st.session_state.get(preco_ref_key_dj) != modelo_disjuntor
                    ):
                        st.session_state[preco_key_dj] = preco_padrao_texto_dj
                        st.session_state[preco_ref_key_dj] = modelo_disjuntor
                    with col_preco:
                        preco_input_dj = st.text_input(
                            "Preço unitário",
                            value=st.session_state.get(preco_key_dj, ""),
                            key=preco_key_dj,
                            placeholder="R$ 0,00",
                        )
                        preco_valor_dj = _parse_float_field(preco_input_dj)
                    if quantidade_key_dj not in st.session_state:
                        st.session_state[quantidade_key_dj] = "1"
                    with col_qtd:
                        quantidade_input_dj = st.text_input(
                            "Quantidade",
                            key=quantidade_key_dj,
                        )
                        quantidade_valor_dj = _parse_float_field(quantidade_input_dj)
                    total_dj = preco_valor_dj * quantidade_valor_dj
                    with col_total:
                        if total_dj > 0:
                            st.write(f"Total: {format_currency(total_dj)}")
                        else:
                            st.write("Total:")
                    if total_dj > 0:
                        total_material_adicional_valor += total_dj
                        material_adicional_dados.append(
                            {
                                "Item": (
                                    f"Disjuntor Caixa Moldada - {modelo_disjuntor}"
                                    if modelo_disjuntor
                                    else "Disjuntor Caixa Moldada"
                                ),
                                "Bitola (mm²)": "",
                                "Valor Unitário": format_currency(preco_valor_dj),
                                "Quantidade (m)": f"{quantidade_valor_dj:.2f}",
                                "Total": format_currency(total_dj),
                            }
                        )

                if st.session_state.get("barra_roscada") == "Sim":
                    st.markdown("**Barra Roscada (vergalhão)**")
                    barra_fallback = [
                        {
                            "Material": "Barra Roscada 1/4",
                            "Preco": 16.00,
                        }
                    ]
                    df_barra = _load_price_table(
                        "valores_barra_roscada_df",
                        "valores_barra_roscada_editor",
                        "valores_barra_roscada.csv",
                        barra_fallback,
                    )
                    opcoes_barra = [""]
                    if not df_barra.empty and "Material" in df_barra.columns:
                        opcoes_barra.extend(
                            [
                                str(material)
                                for material in df_barra["Material"]
                                .dropna()
                                .astype(str)
                                .unique()
                            ]
                        )
                    barra_key = "barra_roscada_material_custos"
                    _sync_selectbox_state(
                        barra_key,
                        "barra_roscada_material",
                        opcoes_barra,
                    )
                    col_item, col_preco, col_qtd, col_total = st.columns([3, 2, 1, 1])
                    with col_item:
                        barra_material = st.selectbox(
                            "Material",
                            opcoes_barra,
                            key=barra_key,
                        )
                    preco_key_barra = "custos_preco_barra_roscada"
                    preco_ref_key_barra = "custos_preco_barra_roscada_ref"
                    quantidade_key_barra = "custos_quantidade_barra_roscada"
                    preco_padrao_barra = 0.0
                    barra_lookup = barra_material
                    linha_barra = pd.DataFrame()
                    if (
                        barra_material
                        and not df_barra.empty
                        and "Material" in df_barra.columns
                    ):
                        if barra_lookup and " - " in barra_lookup:
                            barra_lookup = barra_lookup.split(" - ", 1)[0].strip()
                        linha_barra = df_barra[
                            df_barra["Material"].astype(str) == barra_lookup
                        ]
                        if not linha_barra.empty:
                            preco_padrao_barra = float(
                                linha_barra.iloc[0]["_PrecoNumerico"]
                            )
                    preco_padrao_texto_barra = (
                        format_currency(preco_padrao_barra)
                        if preco_padrao_barra > 0
                        else ""
                    )
                    barra_display = barra_material or ""
                    if (
                        barra_display
                        and " - " not in barra_display
                        and not linha_barra.empty
                    ):
                        preco_texto_original = str(
                            linha_barra.iloc[0].get("Preco", "")
                        ).strip()
                        if preco_texto_original:
                            barra_display = f"{barra_lookup} - {preco_texto_original}"
                    barra_material = barra_display
                    if preco_key_barra not in st.session_state:
                        st.session_state[preco_key_barra] = preco_padrao_texto_barra
                    if (
                        preco_padrao_texto_barra
                        and st.session_state.get(preco_ref_key_barra) != barra_material
                    ):
                        st.session_state[preco_key_barra] = preco_padrao_texto_barra
                        st.session_state[preco_ref_key_barra] = barra_material
                    with col_preco:
                        preco_input_barra = st.text_input(
                            "Preço unitário",
                            value=st.session_state.get(preco_key_barra, ""),
                            key=preco_key_barra,
                            placeholder="R$ 0,00",
                        )
                        preco_valor_barra = _parse_float_field(preco_input_barra)
                    if quantidade_key_barra not in st.session_state:
                        st.session_state[quantidade_key_barra] = "1"
                    with col_qtd:
                        quantidade_input_barra = st.text_input(
                            "Quantidade",
                            key=quantidade_key_barra,
                        )
                        quantidade_valor_barra = _parse_float_field(
                            quantidade_input_barra
                        )
                    total_barra = preco_valor_barra * quantidade_valor_barra
                    with col_total:
                        if total_barra > 0:
                            st.write(f"Total: {format_currency(total_barra)}")
                        else:
                            st.write("Total:")
                    if total_barra > 0:
                        total_material_adicional_valor += total_barra
                        material_adicional_dados.append(
                            {
                                "Item": (
                                    f"Barra Roscada - {barra_material}"
                                    if barra_material
                                    else "Barra Roscada"
                                ),
                                "Bitola (mm²)": "",
                                "Valor Unitário": format_currency(preco_valor_barra),
                                "Quantidade (m)": f"{quantidade_valor_barra:.2f}",
                                "Total": format_currency(total_barra),
                            }
                        )

                if st.session_state.get("eletrocalha") == "Sim":
                    st.markdown("**Eletrocalha**")
                    eletrocalha_fallback = [
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
                    df_eletrocalha = _load_price_table(
                        "valores_eletrocalhas_df",
                        "valores_eletrocalhas_editor",
                        "valores_eletrocalhas.csv",
                        eletrocalha_fallback,
                    )
                    opcoes_eletrocalha = [""]
                    if not df_eletrocalha.empty and "Material" in df_eletrocalha.columns:
                        opcoes_eletrocalha.extend(
                            [
                                str(material)
                                for material in df_eletrocalha["Material"]
                                .dropna()
                                .astype(str)
                                .unique()
                            ]
                        )
                    eletrocalha_key = "custos_material_eletrocalha"
                    _sync_selectbox_state(
                        eletrocalha_key,
                        "dimensoes_eletrocalha",
                        opcoes_eletrocalha,
                    )
                    col_item, col_preco, col_qtd, col_total = st.columns([3, 2, 1, 1])
                    with col_item:
                        eletrocalha_material = st.selectbox(
                            "Dimensão",
                            opcoes_eletrocalha,
                            key=eletrocalha_key,
                        )
                        st.session_state["dimensoes_eletrocalha"] = eletrocalha_material
                    preco_key_eletrocalha = "custos_preco_eletrocalha"
                    preco_ref_key_eletrocalha = "custos_preco_eletrocalha_ref"
                    quantidade_key_eletrocalha = "custos_quantidade_eletrocalha"
                    metros_eletrocalha = st.session_state.get("metros_eletrocalha", 0.0)
                    try:
                        metros_padrao = float(metros_eletrocalha)
                    except (TypeError, ValueError):
                        metros_padrao = 0.0
                    metros_texto = f"{metros_padrao:g}" if metros_padrao else ""
                    if quantidade_key_eletrocalha not in st.session_state:
                        st.session_state[quantidade_key_eletrocalha] = (
                            metros_texto or "1"
                        )
                    else:
                        ref_key = "custos_quantidade_eletrocalha_ref"
                        if metros_texto and st.session_state.get(ref_key) != metros_texto:
                            st.session_state[quantidade_key_eletrocalha] = metros_texto
                            st.session_state[ref_key] = metros_texto
                    preco_padrao_eletrocalha = 0.0
                    if (
                        eletrocalha_material
                        and not df_eletrocalha.empty
                        and "Material" in df_eletrocalha.columns
                    ):
                        linha_eletrocalha = df_eletrocalha[
                            df_eletrocalha["Material"].astype(str)
                            == eletrocalha_material
                        ]
                        if not linha_eletrocalha.empty:
                            preco_padrao_eletrocalha = float(
                                linha_eletrocalha.iloc[0]["_PrecoNumerico"]
                            )
                    preco_padrao_texto_eletrocalha = (
                        format_currency(preco_padrao_eletrocalha)
                        if preco_padrao_eletrocalha > 0
                        else ""
                    )
                    if preco_key_eletrocalha not in st.session_state:
                        st.session_state[preco_key_eletrocalha] = preco_padrao_texto_eletrocalha
                    if (
                        preco_padrao_texto_eletrocalha
                        and st.session_state.get(preco_ref_key_eletrocalha)
                        != eletrocalha_material
                    ):
                        st.session_state[preco_key_eletrocalha] = preco_padrao_texto_eletrocalha
                        st.session_state[preco_ref_key_eletrocalha] = eletrocalha_material
                    with col_preco:
                        preco_input_eletrocalha = st.text_input(
                            "Preço unitário",
                            value=st.session_state.get(preco_key_eletrocalha, ""),
                            key=preco_key_eletrocalha,
                            placeholder="R$ 0,00",
                        )
                        preco_valor_eletrocalha = _parse_float_field(
                            preco_input_eletrocalha
                        )
                    with col_qtd:
                        quantidade_input_eletrocalha = st.text_input(
                            "Quantidade (m)",
                            key=quantidade_key_eletrocalha,
                        )
                        quantidade_valor_eletrocalha = _parse_float_field(
                            quantidade_input_eletrocalha
                        )
                    total_eletrocalha = (
                        preco_valor_eletrocalha * quantidade_valor_eletrocalha
                    )
                    with col_total:
                        if total_eletrocalha > 0:
                            st.write(
                                f"Total: {format_currency(total_eletrocalha)}"
                            )
                        else:
                            st.write("Total:")
                    if total_eletrocalha > 0:
                        total_material_adicional_valor += total_eletrocalha
                        material_adicional_dados.append(
                            {
                                "Item": (
                                    f"Eletrocalha - {eletrocalha_material}"
                                    if eletrocalha_material
                                    else "Eletrocalha"
                                ),
                                "Bitola (mm²)": "",
                                "Valor Unitário": format_currency(
                                    preco_valor_eletrocalha
                                ),
                                "Quantidade (m)": f"{quantidade_valor_eletrocalha:.2f}",
                                "Total": format_currency(total_eletrocalha),
                            }
                        )

                if st.session_state.get("tem_tomada_industrial") == "Sim":
                    st.markdown("**Tomada industrial**")
                    tomada_fallback = [
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
                    df_tomadas = _load_price_table(
                        "valores_tomadas_industriais_df",
                        "valores_tomadas_industriais_editor",
                        "valores_tomadas_industriais.csv",
                        tomada_fallback,
                    )
                    opcoes_tomadas = [""]
                    if not df_tomadas.empty and "Material" in df_tomadas.columns:
                        opcoes_tomadas.extend(
                            [
                                str(material)
                                for material in df_tomadas["Material"]
                                .dropna()
                                .astype(str)
                                .unique()
                            ]
                        )
                    tomada_key = "tomada_industrial_material_custos"
                    _sync_selectbox_state(
                        tomada_key,
                        "tomada_industrial",
                        opcoes_tomadas,
                    )
                    col_item, col_preco, col_qtd, col_total = st.columns([3, 2, 1, 1])
                    with col_item:
                        tomada_material = st.selectbox(
                            "Modelo",
                            opcoes_tomadas,
                            key=tomada_key,
                            on_change=_create_selectbox_sync_callback(
                                tomada_key, "tomada_industrial"
                            ),
                        )
                    preco_key_tomada = "custos_preco_tomada_industrial"
                    preco_ref_key_tomada = "custos_preco_tomada_industrial_ref"
                    quantidade_key_tomada = "custos_quantidade_tomada_industrial"
                    preco_padrao_tomada = 0.0
                    if (
                        tomada_material
                        and not df_tomadas.empty
                        and "Material" in df_tomadas.columns
                    ):
                        linha_tomada = df_tomadas[
                            df_tomadas["Material"].astype(str) == tomada_material
                        ]
                        if not linha_tomada.empty:
                            preco_padrao_tomada = float(
                                linha_tomada.iloc[0]["_PrecoNumerico"]
                            )
                    preco_padrao_texto_tomada = (
                        format_currency(preco_padrao_tomada)
                        if preco_padrao_tomada > 0
                        else ""
                    )
                    if preco_key_tomada not in st.session_state:
                        st.session_state[preco_key_tomada] = preco_padrao_texto_tomada
                    if (
                        preco_padrao_texto_tomada
                        and st.session_state.get(preco_ref_key_tomada)
                        != tomada_material
                    ):
                        st.session_state[preco_key_tomada] = preco_padrao_texto_tomada
                        st.session_state[preco_ref_key_tomada] = tomada_material
                    with col_preco:
                        preco_input_tomada = st.text_input(
                            "Preço unitário",
                            value=st.session_state.get(preco_key_tomada, ""),
                            key=preco_key_tomada,
                            placeholder="R$ 0,00",
                        )
                        preco_valor_tomada = _parse_float_field(preco_input_tomada)
                    if quantidade_key_tomada not in st.session_state:
                        st.session_state[quantidade_key_tomada] = "1"
                    with col_qtd:
                        quantidade_input_tomada = st.text_input(
                            "Quantidade",
                            key=quantidade_key_tomada,
                        )
                        quantidade_valor_tomada = _parse_float_field(
                            quantidade_input_tomada
                        )
                    total_tomada = preco_valor_tomada * quantidade_valor_tomada
                    with col_total:
                        if total_tomada > 0:
                            st.write(f"Total: {format_currency(total_tomada)}")
                        else:
                            st.write("Total:")
                    if total_tomada > 0:
                        total_material_adicional_valor += total_tomada
                        material_adicional_dados.append(
                            {
                                "Item": (
                                    f"Tomada industrial - {tomada_material}"
                                    if tomada_material
                                    else "Tomada industrial"
                                ),
                                "Bitola (mm²)": "",
                                "Valor Unitário": format_currency(
                                    preco_valor_tomada
                                ),
                                "Quantidade (m)": f"{quantidade_valor_tomada:.2f}",
                                "Total": format_currency(total_tomada),
                            }
                        )

                if st.session_state.get("tem_medidor") == "Sim":
                    st.markdown("**Medidor**")
                    medidor_fallback = [
                        {"Material": "Medidor Bipolar Wifi", "Preco": 229.00},
                        {"Material": "Medidor Bipolar", "Preco": 349.50},
                    ]
                    df_medidores = _load_price_table(
                        "valores_medidores_df",
                        "valores_medidores_editor",
                        "valores_medidores.csv",
                        medidor_fallback,
                    )
                    opcoes_medidores = [""]
                    if not df_medidores.empty and "Material" in df_medidores.columns:
                        opcoes_medidores.extend(
                            [
                                str(material)
                                for material in df_medidores["Material"]
                                .dropna()
                                .astype(str)
                                .unique()
                            ]
                        )
                    medidor_key = "medidor_material_custos"
                    _sync_selectbox_state(
                        medidor_key,
                        "medidor",
                        opcoes_medidores,
                    )
                    col_item, col_preco, col_qtd, col_total = st.columns([3, 2, 1, 1])
                    with col_item:
                        medidor_material = st.selectbox(
                            "Modelo",
                            opcoes_medidores,
                            key=medidor_key,
                            on_change=_create_selectbox_sync_callback(
                                medidor_key, "medidor"
                            ),
                        )
                    preco_key_medidor = "custos_preco_medidor"
                    preco_ref_key_medidor = "custos_preco_medidor_ref"
                    quantidade_key_medidor = "custos_quantidade_medidor"
                    preco_padrao_medidor = 0.0
                    if (
                        medidor_material
                        and not df_medidores.empty
                        and "Material" in df_medidores.columns
                    ):
                        linha_medidor = df_medidores[
                            df_medidores["Material"].astype(str)
                            == medidor_material
                        ]
                        if not linha_medidor.empty:
                            preco_padrao_medidor = float(
                                linha_medidor.iloc[0]["_PrecoNumerico"]
                            )
                    preco_padrao_texto_medidor = (
                        format_currency(preco_padrao_medidor)
                        if preco_padrao_medidor > 0
                        else ""
                    )
                    if preco_key_medidor not in st.session_state:
                        st.session_state[preco_key_medidor] = (
                            preco_padrao_texto_medidor
                        )
                    if (
                        preco_padrao_texto_medidor
                        and st.session_state.get(preco_ref_key_medidor)
                        != medidor_material
                    ):
                        st.session_state[preco_key_medidor] = (
                            preco_padrao_texto_medidor
                        )
                        st.session_state[preco_ref_key_medidor] = medidor_material
                    with col_preco:
                        preco_input_medidor = st.text_input(
                            "Preço unitário",
                            value=st.session_state.get(preco_key_medidor, ""),
                            key=preco_key_medidor,
                            placeholder="R$ 0,00",
                        )
                        preco_valor_medidor = _parse_float_field(preco_input_medidor)
                    if quantidade_key_medidor not in st.session_state:
                        st.session_state[quantidade_key_medidor] = "1"
                    with col_qtd:
                        quantidade_input_medidor = st.text_input(
                            "Quantidade",
                            key=quantidade_key_medidor,
                        )
                        quantidade_valor_medidor = _parse_float_field(
                            quantidade_input_medidor
                        )
                    total_medidor = preco_valor_medidor * quantidade_valor_medidor
                    with col_total:
                        if total_medidor > 0:
                            st.write(f"Total: {format_currency(total_medidor)}")
                        else:
                            st.write("Total:")
                    if total_medidor > 0:
                        total_material_adicional_valor += total_medidor
                        material_adicional_dados.append(
                            {
                                "Item": (
                                    f"Medidor - {medidor_material}"
                                    if medidor_material
                                    else "Medidor"
                                ),
                                "Bitola (mm²)": "",
                                "Valor Unitário": format_currency(
                                    preco_valor_medidor
                                ),
                                "Quantidade (m)": f"{quantidade_valor_medidor:.2f}",
                                "Total": format_currency(total_medidor),
                            }
                        )

                if st.session_state.get("transformador") == "Sim":
                    st.markdown("**Transformador**")

                    transformadores_padrao = obter_transformadores_padrao()
                    produtos_transformadores = st.session_state.get(
                        "transformadores_produtos",
                        [
                            item.get("Produto", "")
                            for item in transformadores_padrao
                            if item.get("Produto")
                        ],
                    )
                    produtos_transformadores = [
                        produto for produto in produtos_transformadores if produto
                    ]
                    opcoes_transformador = [""] + produtos_transformadores

                    transformador_key = "transformador_material_custos"
                    _sync_selectbox_state(
                        transformador_key,
                        "transformador_produto",
                        opcoes_transformador,
                    )

                    col_item, col_preco, col_qtd, col_total = st.columns([3, 2, 1, 1])

                    with col_item:
                        transformador_material = st.selectbox(
                            "Modelo",
                            opcoes_transformador,
                            key=transformador_key,
                            on_change=_create_selectbox_sync_callback(
                                transformador_key,
                                "transformador_produto",
                            ),
                        )

                    preco_key_transformador = "custos_preco_transformador"
                    preco_ref_key_transformador = "custos_preco_transformador_ref"
                    quantidade_key_transformador = "custos_quantidade_transformador"

                    preco_padrao_transformador = 0.0
                    if transformador_material:
                        for item in transformadores_padrao:
                            if item.get("Produto") == transformador_material:
                                try:
                                    preco_padrao_transformador = float(
                                        item.get("Preço", 0.0)
                                    )
                                except (TypeError, ValueError):
                                    preco_padrao_transformador = 0.0
                                break

                    preco_padrao_texto_transformador = (
                        format_currency(preco_padrao_transformador)
                        if preco_padrao_transformador > 0
                        else ""
                    )

                    if preco_key_transformador not in st.session_state:
                        st.session_state[
                            preco_key_transformador
                        ] = preco_padrao_texto_transformador

                    if (
                        preco_padrao_texto_transformador
                        and st.session_state.get(preco_ref_key_transformador)
                        != transformador_material
                    ):
                        st.session_state[
                            preco_key_transformador
                        ] = preco_padrao_texto_transformador
                        st.session_state[
                            preco_ref_key_transformador
                        ] = transformador_material

                    with col_preco:
                        preco_input_transformador = st.text_input(
                            "Preço unitário",
                            value=st.session_state.get(
                                preco_key_transformador, ""
                            ),
                            key=preco_key_transformador,
                            placeholder="R$ 0,00",
                        )
                        preco_valor_transformador = _parse_float_field(
                            preco_input_transformador
                        )

                    if quantidade_key_transformador not in st.session_state:
                        st.session_state[quantidade_key_transformador] = "1"

                    with col_qtd:
                        quantidade_input_transformador = st.text_input(
                            "Quantidade",
                            key=quantidade_key_transformador,
                        )
                        quantidade_valor_transformador = _parse_float_field(
                            quantidade_input_transformador
                        )

                    total_transformador = (
                        preco_valor_transformador * quantidade_valor_transformador
                    )

                    with col_total:
                        if total_transformador > 0:
                            st.write(
                                f"Total: {format_currency(total_transformador)}"
                            )
                        else:
                            st.write("Total:")

                    if total_transformador > 0:
                        total_material_adicional_valor += total_transformador
                        material_adicional_dados.append(
                            {
                                "Item": (
                                    f"Transformador - {transformador_material}"
                                    if transformador_material
                                    else "Transformador"
                                ),
                                "Bitola (mm²)": "",
                                "Valor Unitário": format_currency(
                                    preco_valor_transformador
                                ),
                                "Quantidade (m)": f"{quantidade_valor_transformador:.2f}",
                                "Total": format_currency(total_transformador),
                            }
                        )

                if st.session_state.get("totem") == "Sim":
                    st.markdown("**Totem**")

                    descricao_key_totem = "totem_descricao_custos"
                    if descricao_key_totem not in st.session_state:
                        st.session_state[descricao_key_totem] = "Totem"

                    preco_key_totem = "custos_preco_totem"
                    quantidade_key_totem = "custos_quantidade_totem"

                    col_item, col_preco, col_qtd, col_total = st.columns([3, 2, 1, 1])

                    with col_item:
                        descricao_totem = st.text_input(
                            "Descrição",
                            key=descricao_key_totem,
                        )

                    with col_preco:
                        preco_input_totem = st.text_input(
                            "Preço unitário",
                            value=st.session_state.get(preco_key_totem, ""),
                            key=preco_key_totem,
                            placeholder="R$ 0,00",
                        )
                        preco_valor_totem = _parse_float_field(preco_input_totem)

                    if quantidade_key_totem not in st.session_state:
                        st.session_state[quantidade_key_totem] = "1"

                    with col_qtd:
                        quantidade_input_totem = st.text_input(
                            "Quantidade",
                            key=quantidade_key_totem,
                        )
                        quantidade_valor_totem = _parse_float_field(
                            quantidade_input_totem
                        )

                    total_totem = preco_valor_totem * quantidade_valor_totem

                    with col_total:
                        if total_totem > 0:
                            st.write(f"Total: {format_currency(total_totem)}")
                        else:
                            st.write("Total:")

                    if total_totem > 0:
                        total_material_adicional_valor += total_totem
                        material_adicional_dados.append(
                            {
                                "Item": descricao_totem.strip()
                                if descricao_totem.strip()
                                else "Totem",
                                "Bitola (mm²)": "",
                                "Valor Unitário": format_currency(
                                    preco_valor_totem
                                ),
                                "Quantidade (m)": f"{quantidade_valor_totem:.2f}",
                                "Total": format_currency(total_totem),
                            }
                        )

                if total_material_adicional_valor > 0:
                    st.write(
                        f"Total Material Adicional: {format_currency(total_material_adicional_valor)}"
                    )

            st.session_state["total_material_adicional"] = total_material_adicional_valor
        else:
            st.session_state["total_material_adicional"] = 0.0

        total_materiais_valor = (
            total_cabos_valor
            + total_infra_seca_valor
            + total_quadro_protecao_valor
            + total_material_adicional_valor
        )
        st.markdown(
            f"<p style='color: green; font-size: 40px;'>💰 Total Custos com Materiais: {format_currency(total_materiais_valor)}</p>",
            unsafe_allow_html=True,
        )
        st.session_state["total_custos_materiais"] = total_materiais_valor

        blocos_totais = [
            ("Cabos", total_cabos_valor),
            ("Infra-Seca", total_infra_seca_valor),
            ("Quadro de Proteção", total_quadro_protecao_valor),
            ("Material Adicional", total_material_adicional_valor),
        ]
        df_blocos = pd.DataFrame(blocos_totais, columns=["Bloco", "Valor"])
        df_blocos = df_blocos[df_blocos["Valor"] > 0]

        render_pizza_custos_materiais(df_blocos, format_currency)

        relatorio_dados = cabos_dados.copy()
        if quadro_dados:
            relatorio_dados.extend(quadro_dados)
        if material_adicional_dados:
            relatorio_dados.extend(material_adicional_dados)
        infra_dados = []
        if total_infra_valor > 0:
            infra_dados.append(
                {
                    "Item": material_eletroduto,
                    "Bitola (mm²)": "",
                    "Valor Unitário": format_currency(preco_eletroduto),
                    "Quantidade (m)": f"{metragem_eletroduto:.2f}",
                    "Total": format_currency(total_infra_valor),
                }
            )
        if total_condulete_valor > 0:
            infra_dados.append(
                {
                    "Item": material_condulete,
                    "Bitola (mm²)": "",
                    "Valor Unitário": format_currency(preco_condulete),
                    "Quantidade (m)": f"{qtd_condulete:.2f}",
                    "Total": format_currency(total_condulete_valor),
                }
            )
        if total_condulete_t_valor > 0:
            infra_dados.append(
                {
                    "Item": material_condulete_t,
                    "Bitola (mm²)": "",
                    "Valor Unitário": format_currency(preco_condulete_t),
                    "Quantidade (m)": f"{qtd_condulete_t:.2f}",
                    "Total": format_currency(total_condulete_t_valor),
                }
            )
        if total_unidut_reto_valor > 0:
            infra_dados.append(
                {
                    "Item": material_unidut_reto,
                    "Bitola (mm²)": "",
                    "Valor Unitário": format_currency(preco_unidut_reto),
                    "Quantidade (m)": f"{qtd_unidut_reto:.2f}",
                    "Total": format_currency(total_unidut_reto_valor),
                }
            )
        if total_unidut_conico_valor > 0:
            infra_dados.append(
                {
                    "Item": material_unidut_conico,
                    "Bitola (mm²)": "",
                    "Valor Unitário": format_currency(preco_unidut_conico),
                    "Quantidade (m)": f"{qtd_unidut_conico:.2f}",
                    "Total": format_currency(total_unidut_conico_valor),
                }
            )
        if total_curva_valor > 0:
            infra_dados.append(
                {
                    "Item": material_curva,
                    "Bitola (mm²)": "",
                    "Valor Unitário": format_currency(preco_curva),
                    "Quantidade (m)": f"{qtd_curva:.2f}",
                    "Total": format_currency(total_curva_valor),
                }
            )
        if total_unilet_valor > 0:
            infra_dados.append(
                {
                    "Item": material_unilet,
                    "Bitola (mm²)": "",
                    "Valor Unitário": format_currency(preco_unilet),
                    "Quantidade (m)": f"{qtd_unilet:.2f}",
                    "Total": format_currency(total_unilet_valor),
                }
            )
        if total_abracadeira_valor > 0:
            infra_dados.append(
                {
                    "Item": material_abracadeira,
                    "Bitola (mm²)": "",
                    "Valor Unitário": format_currency(preco_abracadeira),
                    "Quantidade (m)": f"{qtd_abracadeira:.2f}",
                    "Total": format_currency(total_abracadeira_valor),
                }
            )
        if total_sealtubo_valor > 0:
            infra_dados.append(
                {
                    "Item": material_sealtubo,
                    "Bitola (mm²)": "",
                    "Valor Unitário": format_currency(preco_sealtubo),
                    "Quantidade (m)": f"{qtd_sealtubo:.2f}",
                    "Total": format_currency(total_sealtubo_valor),
                }
            )

        relatorio_dados.extend(infra_dados)
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
                    label="Salvar Relatório de Custos com Materiais",
                    data=buffer.getvalue(),
                    file_name="relatorio_custos_materiais.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    ),
                )
