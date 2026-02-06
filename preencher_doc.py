from pathlib import Path
from datetime import datetime

import streamlit as st
from docxtpl import DocxTemplate


# Carrega o template .docx com o "papel timbrado"
TEMPLATE_NAME = "Modelo Doc papel timbrado.docx"
template_path = Path(__file__).with_name(TEMPLATE_NAME)
doc = DocxTemplate(template_path)

# Campo de entrada no formulário para o nome do cliente
st.text_input("Nome do Cliente", key="cliente")

# Gera o documento preenchido quando o usuário clicar no botão
if st.button("Gerar Documento"):
    cliente = st.session_state["cliente"]
    tensao = st.session_state.get("tensao_carregador_orcamento", "")
    possui_carregador = st.session_state.get("possui_carregador", "")
    data_atual = datetime.now().strftime("%d/%m/%Y")
    def format_currency(value: float) -> str:
        """Format number as Brazilian Real currency."""

        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # Valores provenientes da aba "Cálculo de serviço"
    # Mantêm os mesmos padrões definidos nos campos correspondentes caso o usuário
    # ainda não tenha interagido com eles durante a sessão.
    valor_trt = st.session_state.get("custo_emissao_trt", 80.0)
    valor_projeto = st.session_state.get("custo_projeto_unifilar", 500.0)

    condicoes_pagamento_carregador = ""
    if possui_carregador == "Não":
        condicoes_pagamento_carregador = (
            "O pagamento do valor correspondente ao carregador deverá ser efetuado de forma antecipada, à vista."
        )

    contexto = {
        "nome_do_cliente": cliente,
        "tensao": tensao,
        "data": data_atual,
        "valor-trt": format_currency(valor_trt),
        "valor-projeto": format_currency(valor_projeto),
        "valor_trt": format_currency(valor_trt),
        "valor_projeto": format_currency(valor_projeto),
        "condicoes_de_pagamento_carregador": condicoes_pagamento_carregador,
    }
    doc.render(contexto)
    doc.save("documento_final.docx")
    st.success("Documento gerado!")

