import importlib.util
import io
import re
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

DOCXTPL_MISSING_MESSAGE = (
    "O pacote 'docxtpl' é necessário para gerar o documento de orçamento. "
    "Instale-o com 'pip install docxtpl'."
)
_DOCXTPL_IMPORT_ERROR = None
_DOCXTPL_SPEC = importlib.util.find_spec("docxtpl")
if _DOCXTPL_SPEC:
    from docxtpl import DocxTemplate, RichText
else:
    DocxTemplate = None
    RichText = None
    _DOCXTPL_IMPORT_ERROR = ModuleNotFoundError("docxtpl")

# Caminhos dos templates .docx utilizando o mesmo diretório deste arquivo
_TEMPLATE_PATHS = {
    "default": Path(__file__).with_name(
        "Modelo Proposta Técnica e Comercial - CE ALFERION.docx"
    ),
    "Análise de Energia": Path(__file__).with_name(
        "Modelo Proposta Técnica e Comercial - AE ALFERION.docx"
    ),
    "Manutenção Corretiva": Path(__file__).with_name(
        "Modelo Proposta Técnica e Comercial - MC ALFERION.docx"
    ),
}

# Texto descritivo para cada condição de pagamento disponível
CONDICOES_PAGAMENTO_TEXT = {
    "50% antecipado e 50% em 15 dias": (
        "O valor total do serviço poderá ser dividido em 2 parcelas sem juros, sendo a primeira "
        "parcela antecipada no valor de 50% através de depósito bancário; e a segunda parcela de 50% em até 15 dias "
        "da instalação e comissionamento do equipamento. Para pagamento à vista, através de depósito bancário "
        "antecipado, poderá ser concedido 5% de desconto no valor total."
    ),
    "A Vista antecipado": (
        "O valor total do serviço deverá ser pago a vista antecipado através de depósito bancário."
    ),
    "A Vista ao final do serviço": (
        "O valor total do serviço deverá ser pago a vista através de depósito bancário ao termino do serviço"
    ),
    "Wecharge": (
        "O valor total do serviço deverá ser pago via boleto em até 30 dias a partir da emissão da nota fiscal."
    ),
}

# Texto descritivo para cada serviço disponível
ANALISE_ENERGIA_FALLBACK_TEXT = (
    "A ALFERION oferece o serviço de análise completa de energia elétrica, "
    "utilizando o analisador profissional EMI P500R V2 da ISSO, que permite "
    "medições precisas e relatórios detalhados sobre a qualidade e eficiência "
    "energética das instalações.\n"
    "\n"
    "O serviço de análise contempla:\n"
    "\n"
    "1. Medições em Campo\n"
    "\t• Monitoramento de tensão, corrente e potência em tempo real.\n"
    "\t• Levantamento de distorções harmônicas, fator de potência e energia reativa.\n"
    "\t• Registro de eventos transitórios, oscilações e picos de tensão.\n"
    "\n"
    "2. Estudos Técnicos\n"
    "\t• Identificação de perdas elétricas.\n"
    "\t• Diagnóstico de possíveis causas de falhas e mau funcionamento em equipamentos.\n"
    "\n"
    "3. Relatório Técnico Detalhado\n"
    "\t• Apresentação gráfica e tabulada de todos os parâmetros coletados.\n"
    "\t• Identificação de problemas de qualidade de energia (como harmônicas, "
    "desequilíbrios, subtensões e sobretensões).\n"
    "\t• Propostas de melhorias para eficiência energética e segurança operacional.\n"
    "\n"
    "4. Recomendações e Consultoria\n"
    "\t• Sugestão de correções e adequações na instalação elétrica.\n"
    "\t• Orientações sobre manutenções preventivas e corretivas.\n"
)

DESCRICAO_SERVICOS_TEXT = {
    "Instalação": (
        "Os serviços contemplados nesta proposta incluem a avaliação técnica e "
        "financeira da instalação, a escolha do carregador mais adequado às "
        "necessidades do cliente, o dimensionamento e adequação do circuito "
        "elétrico conforme as normas vigentes, a instalação e configuração do "
        "equipamento, além da orientação completa para o uso correto e seguro "
        "do carregador."
    ),
    "Manutenção": (
        "Os serviços contemplados nesta proposta incluem a análise da "
        "infraestrutura e carregador para identificar causas do defeito no "
        "aparelho. Caso seja possível a corretiva será feita na hora. Caso "
        "exija compra de equipamento adicional a proposta será atualizada."
    ),
    "Manutenção Preventiva": "Escrever texto.",
    "Manutenção Corretiva": "Escrever texto 2.",
    "Análise de Energia": ANALISE_ENERGIA_FALLBACK_TEXT,
}


def _build_analise_energia_richtext():
    if RichText is None:
        return ANALISE_ENERGIA_FALLBACK_TEXT

    rt = RichText()
    rt.add("A ")
    rt.add("ALFERION", bold=True)
    rt.add(
        " oferece o serviço de análise completa de energia elétrica, utilizando o analisador "
        "profissional "
    )
    rt.add("EMI P500R V2 da ISSO", bold=True)
    rt.add(
        ", que permite medições precisas e relatórios detalhados sobre a qualidade e "
        "eficiência energética das instalações."
    )
    rt.add("\n\n")
    rt.add("O serviço de análise contempla:\n\n")

    sections = [
        (
            "1.",
            "Medições em Campo",
            [
                "Monitoramento de tensão, corrente e potência em tempo real.",
                "Levantamento de distorções harmônicas, fator de potência e energia reativa.",
                "Registro de eventos transitórios, oscilações e picos de tensão.",
            ],
        ),
        (
            "2.",
            "Estudos Técnicos",
            [
                "Identificação de perdas elétricas.",
                "Diagnóstico de possíveis causas de falhas e mau funcionamento em equipamentos.",
            ],
        ),
        (
            "3.",
            "Relatório Técnico Detalhado",
            [
                "Apresentação gráfica e tabulada de todos os parâmetros coletados.",
                "Identificação de problemas de qualidade de energia (como harmônicas, "
                "desequilíbrios, subtensões e sobretensões).",
                "Propostas de melhorias para eficiência energética e segurança operacional.",
            ],
        ),
        (
            "4.",
            "Recomendações e Consultoria",
            [
                "Sugestão de correções e adequações na instalação elétrica.",
                "Orientações sobre manutenções preventivas e corretivas.",
            ],
        ),
    ]

    for index, (number, title, bullets) in enumerate(sections):
        rt.add(f"{number} ")
        rt.add(title, bold=True)
        rt.add("\n")
        for bullet in bullets:
            rt.add("\t• ")
            rt.add(bullet)
            rt.add("\n")
        if index < len(sections) - 1:
            rt.add("\n")

    return rt

# Texto de garantia para cada serviço disponível
GARANTIA_SERVICOS_TEXT = {
    "Instalação": (
        "Os serviços de instalação terão garantia de 12 meses a contar da data de entrega da instalação. "
        "Todas as nossas instalações são testadas e conferidas com um checklist ao final da instalação, "
        "essa conferência é realizada em conjunto com o cliente, ou representante e documentada por meio de "
        "assinatura, ou vídeo. Falhas ou defeitos no carregador, após a instalação, não são de responsabilidade "
        "da ALFERION. Ainda assim é possível oferecer suporte técnico para qualquer eventual dano no equipamento, "
        "isto, porém, estará fora da cobertura da garantia da instalação, devendo assim ter custos referente a esse "
        "trabalho especializado."
    ),
    "Manutenção": (
        "Os serviços de manutenção terão garantia de 3 meses a contar da data da execução do serviço. "
        "Todas as nossos serviços são testados e conferidas com um checklist, essa conferência é realizada em conjunto "
        "com o cliente, ou representante e documentada por meio de assinatura, ou vídeo. Falhas ou defeitos no carregador, "
        "após a manutenção, ocasionados por mau uso, não são de responsabilidade da ALFERION. Ainda assim é possível "
        "oferecer suporte técnico para qualquer eventual dano no equipamento, isto, porém, estará fora da cobertura da "
        "garantia da manutenção, devendo assim ter custos referente a esse trabalho especializado."
    ),
    "Manutenção Preventiva": (
        "Os serviços de manutenção preventiva terão garantia de 3 meses a contar da data da execução do serviço. "
        "Todas as nossas manutenções preventivas são testadas e conferidas com um checklist, essa conferência é realizada "
        "em conjunto com o cliente, ou representante e documentada por meio de assinatura, ou vídeo. Falhas ou defeitos no "
        "carregador, após a manutenção preventiva, ocasionados por mau uso, não são de responsabilidade da ALFERION. Ainda "
        "assim é possível oferecer suporte técnico para qualquer eventual dano no equipamento, isto, porém, estará fora da "
        "cobertura da garantia da manutenção preventiva, devendo assim ter custos referente a esse trabalho especializado."
    ),
    "Manutenção Corretiva": (
        "Os serviços de manutenção corretiva terão garantia de 3 meses a contar da data da execução do serviço. "
        "Todas as nossas manutenções corretivas são testadas e conferidas com um checklist, essa conferência é realizada em "
        "conjunto com o cliente, ou representante e documentada por meio de assinatura, ou vídeo. Falhas ou defeitos no "
        "carregador, após a manutenção corretiva, ocasionados por mau uso, não são de responsabilidade da ALFERION. Ainda "
        "assim é possível oferecer suporte técnico para qualquer eventual dano no equipamento, isto, porém, estará fora da "
        "cobertura da garantia da manutenção corretiva, devendo assim ter custos referente a esse trabalho especializado."
    ),
    "Análise de Energia": (
        "Os serviços de análise de energia terão garantia de 3 meses a contar da entrega do relatório. Todos os procedimentos "
        "são testados e conferidos com um checklist, essa conferência é realizada em conjunto com o cliente, ou representante e "
        "documentada por meio de assinatura, ou vídeo. Divergências posteriores decorrentes de alterações no sistema elétrico "
        "ou mau uso não são de responsabilidade da ALFERION. Ainda assim é possível oferecer suporte técnico para esclarecimentos, "
        "isto, porém, estará fora da cobertura da garantia da análise de energia, devendo assim ter custos referente a esse trabalho "
        "especializado."
    ),
}


def format_currency(value: float) -> str:
    """Format number as Brazilian Real currency."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _parse_to_positive_float(value) -> float:
    """Convert values to a positive float, returning ``0.0`` when parsing fails."""

    if isinstance(value, (int, float)):
        return abs(float(value))

    if isinstance(value, str):
        normalizado = value.replace("R$", "").replace("\u00a0", "").strip()
        normalizado = normalizado.replace(".", "").replace(",", ".")

        try:
            return abs(float(normalizado))
        except ValueError:
            return 0.0

    try:
        return abs(float(value))
    except (TypeError, ValueError):
        return 0.0


def _get_orcamento_template_path(descricao_servicos_opcao: str) -> Path:
    """Seleciona o template conforme a descrição dos serviços."""
    return _TEMPLATE_PATHS.get(descricao_servicos_opcao, _TEMPLATE_PATHS["default"])


def gerar_documento_orcamento() -> io.BytesIO:
    """Gera um documento de orçamento em formato .docx usando um template."""
    total_materiais = st.session_state.get("total_custos_materiais", 0.0)
    total_mao_obra = st.session_state.get("total_custo_mao_obra", 0.0)
    custo_deslocamento = st.session_state.get("total_custo_deslocamento", 0.0)
    total_servico = st.session_state.get("total_calculo_servico", 0.0)
    custo_emissao_trt = st.session_state.get("custo_emissao_trt", 0.0)
    custo_projeto_unifilar = st.session_state.get("custo_projeto_unifilar", 0.0)
    cliente = st.session_state.get("cliente_orcamento", "")
    pronome = st.session_state.get("pronome_orcamento", "")
    descricao_servicos_opcao = st.session_state.get("descricao_servicos", "")
    if descricao_servicos_opcao == "Análise de Energia":
        descricao_servicos = _build_analise_energia_richtext()
    else:
        descricao_servicos = DESCRICAO_SERVICOS_TEXT.get(
            descricao_servicos_opcao, ""
        )
    garantia = GARANTIA_SERVICOS_TEXT.get(descricao_servicos_opcao, "")
    tipo_servico = st.session_state.get("tipo_servico_orcamento", "")
    tempo_estimado = st.session_state.get("tempo_estimado_obra", 0)
    condicoes_pagamento_opcao = st.session_state.get("condicoes_pagamento", "")
    condicoes_pagamento = CONDICOES_PAGAMENTO_TEXT.get(
        condicoes_pagamento_opcao, ""
    )
    dias = f"{tempo_estimado} dia" if tempo_estimado == 1 else f"{tempo_estimado} dias"

    distancia_total_infra = st.session_state.get("distancia_total_infra", "")
    distancia_total_infra_str = f"{distancia_total_infra}" if distancia_total_infra else ""
    soma_parcial_custos = st.session_state.get("soma_parcial_custos")
    total_instalacao = st.session_state.get("total_instalacao_calculo_servico")
    if total_instalacao is None:
        if soma_parcial_custos is not None:
            total_instalacao = format_currency(soma_parcial_custos)
        else:
            total_instalacao = st.session_state.get(
                "total_instalacao", format_currency(total_servico)
            )

    data_atual = datetime.now().strftime("%d/%m/%Y")
    possui_carregador = st.session_state.get("possui_carregador", "")
    condicoes_pagamento_carregador = ""
    preco_unitario_carregador = float(
        st.session_state.get("preco_unitario_carregador", 0.0) or 0.0
    )
    total_carregadores = _parse_to_positive_float(
        st.session_state.get("total_carregadores", 0.0)
    )
    if total_carregadores == 0.0 and preco_unitario_carregador:
        total_carregadores = abs(preco_unitario_carregador)
    dados_carregador = st.session_state.get("carregador_ce_dados", {}) or {}

    if possui_carregador == "Não":
        condicoes_pagamento_carregador = (
            "O pagamento do valor correspondente ao carregador deverá ser efetuado de forma antecipada, à vista."
        )
        marca_carregador = (
            dados_carregador.get("Fabricante")
            or st.session_state.get("marca_carregadores", "")
        )
        modelo_carregador = dados_carregador.get("Modelo", "")
        potencia_carregador = (
            dados_carregador.get("Potência")
            or st.session_state.get("potencia_carregador_orcamento", "")
        )

        descricao_carregador_partes = [
            parte
            for parte in [
                f"Marca: {marca_carregador}" if marca_carregador else "",
                f"Modelo: {modelo_carregador}" if modelo_carregador else "",
                f"Potência: {potencia_carregador}" if potencia_carregador else "",
            ]
            if parte
        ]
        descricao_carregador = (
            " | ".join(descricao_carregador_partes)
            if descricao_carregador_partes
            else "Não informado"
        )

        carregador_label = "Carregador"
        valor_carregador_formatado = format_currency(total_carregadores)
    else:
        descricao_carregador = "Não se aplica"
        carregador_label = "Opcional"
        valor_carregador_formatado = "0"

    contexto = {
        "pronome": pronome,
        "nome_do_cliente": cliente,
        "data": data_atual,
        "total_materiais": format_currency(total_materiais),
        "total_mao_obra": format_currency(total_mao_obra),
        "custo_deslocamento": format_currency(custo_deslocamento),
        "total_servico": format_currency(total_servico),
        "valor_total": format_currency(total_servico),
        "descrição_dos_servicos": descricao_servicos,
        "garantia": garantia,
        "tempo_estimado_para_conclusao_da_obra": dias,
        "dias": dias,
        "Tipo_de_Serviço": tipo_servico,
        "potencia": st.session_state.get("potencia_carregador_orcamento", ""),
        "tensao": st.session_state.get("tensao_carregador_orcamento", ""),
        "distancia": distancia_total_infra_str,
        "total_instalcao": total_instalacao,
        "condicoes_de_pagamento": condicoes_pagamento,
        "valor_trt": format_currency(custo_emissao_trt),
        "valor_projeto": format_currency(custo_projeto_unifilar),
        "carregador": carregador_label,
        "modelo_carregador": descricao_carregador,
        "valor_carregador": valor_carregador_formatado,
        "condicoes_de_pagamento_carregador": condicoes_pagamento_carregador,
    }

    if DocxTemplate is None:
        raise ModuleNotFoundError(
            DOCXTPL_MISSING_MESSAGE
        ) from _DOCXTPL_IMPORT_ERROR

    # Carrega o template localizado no mesmo diretório deste arquivo
    template_path = _get_orcamento_template_path(descricao_servicos_opcao)
    doc = DocxTemplate(template_path)
    doc.render(contexto)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


def _format_date_value(value):
    """Return a human friendly representation for date values."""

    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    return value


def _serialize_percursos(percursos):
    """Join percurso entries in a compact textual representation."""

    if not percursos:
        return ""
    partes = []
    for direcao, distancia in percursos:
        if distancia is None:
            distancia = 0.0
        try:
            distancia_float = float(distancia)
        except (TypeError, ValueError):
            distancia_float = 0.0
        partes.append(f"{direcao} {distancia_float:g} m")
    return " | ".join(partes)


def _collect_visita_report_row():
    """Collect the main inputs from the "Visita" tab for the consolidated report."""

    percursos = st.session_state.get("percursos", [])
    total_distancia = sum(
        float(distancia or 0.0) for _, distancia in percursos
    ) if percursos else 0.0

    row = {
        "Aba": "Visita",
        "Ordem de Venda": st.session_state.get("ordem_venda", ""),
        "Cliente": st.session_state.get("cliente", ""),
        "CPF / CNPJ": st.session_state.get("cpf_cnpj", ""),
        "Endereço": st.session_state.get("endereco", ""),
        "Email": st.session_state.get("email", ""),
        "Tipo de Serviço": st.session_state.get("tipo_servico", ""),
        "Tipo de Local": st.session_state.get("tipo_local", ""),
        "Técnico": st.session_state.get("tecnico", ""),
        "Data da Visita": _format_date_value(st.session_state.get("data_hora")),
        "Deslocamento Necessário": st.session_state.get(
            "deslocamento_necessario", ""
        ),
        "Distância (km)": st.session_state.get("distancia_km", 0.0),
        "Tempo de Viagem": st.session_state.get("tempo_viagem", ""),
        "Custo com Pedágios": st.session_state.get("custo_pedagios", 0.0),
        "Percursos": _serialize_percursos(percursos),
        "Distância Total Percorrida (m)": total_distancia,
        "Possui Carregador": st.session_state.get("possui_carregador", ""),
        "Quantidade de Carregadores": st.session_state.get(
            "quantidade_carregadores", ""
        ),
        "Quadro de distribuição": st.session_state.get(
            "quadro_distribuicao", ""
        ),
        "Potência do Carregador": st.session_state.get(
            "potencia_carregador", ""
        ),
        "Marca dos Carregadores": st.session_state.get(
            "marca_carregadores", ""
        ),
        "Tipo de Conectividade": st.session_state.get(
            "tipo_conectividade", ""
        ),
        "Observações": st.session_state.get("observacoes", "").strip(),
    }
    return row


def _collect_resumo_report_row():
    """Collect the summary information shown in the Dimensionamento tab."""

    percursos = st.session_state.get("percursos", [])
    total_distancia = sum(
        float(distancia or 0.0) for _, distancia in percursos
    ) if percursos else 0.0

    tensoes_ff = {
        "R/S": st.session_state.get("tensao_rs", ""),
        "R/T": st.session_state.get("tensao_rt", ""),
        "S/T": st.session_state.get("tensao_st", ""),
    }
    tensoes_fn = {
        "R/N": st.session_state.get("tensao_rn", ""),
        "S/N": st.session_state.get("tensao_sn", ""),
        "T/N": st.session_state.get("tensao_tn", ""),
    }
    tensoes_ft = {
        "R/T": st.session_state.get("tensao_rtt", ""),
        "S/T": st.session_state.get("tensao_stt", ""),
        "T/T": st.session_state.get("tensao_ttt", ""),
    }
    correntes = {
        "R": st.session_state.get("corrente_r", ""),
        "S": st.session_state.get("corrente_s", ""),
        "T": st.session_state.get("corrente_t", ""),
    }

    dispositivos = []
    if st.session_state.get("dj_disjuntor"):
        dispositivos.append("Disjuntor")
    if st.session_state.get("dj_fusivel"):
        dispositivos.append("Fusível")
    if st.session_state.get("dj_outro"):
        dispositivos.append("Outro")

    row = {
        "Aba": "Resumo",
        "Serviço": st.session_state.get("tipo_servico", ""),
        "Local": st.session_state.get("tipo_local", ""),
        "Possui Carregador": st.session_state.get("possui_carregador", ""),
        "Quantidade de Carregadores": st.session_state.get(
            "quantidade_carregadores", ""
        ),
        "Quadro de distribuição": st.session_state.get(
            "quadro_distribuicao", ""
        ),
        "Potência do Carregador": st.session_state.get(
            "potencia_carregador", ""
        ),
        "Marca dos Carregadores": st.session_state.get(
            "marca_carregadores", ""
        ),
        "Tipo de Conectividade": st.session_state.get(
            "tipo_conectividade", ""
        ),
        "Percursos": _serialize_percursos(percursos),
        "Distância Total Percorrida (m)": total_distancia,
        "Observações": st.session_state.get("observacoes", "").strip(),
        "Alimentação": st.session_state.get("alimentacao", ""),
        "Dispositivos de Proteção": ", ".join(dispositivos),
        "Corrente do Disjuntor": st.session_state.get(
            "corrente_disjuntor", ""
        ),
        "Bitola dos Cabos": st.session_state.get("bitola_cabos", ""),
        "Sistema de Aterramento": st.session_state.get(
            "sistema_aterramento", ""
        ),
        "Barra Neutro/Terra": st.session_state.get("barra_neutro_terra", ""),
        "Espaço DJ Saída": st.session_state.get("espaco_dj_saida", ""),
        "Tensões Fase-Fase": ", ".join(
            f"{fase}: {valor}" for fase, valor in tensoes_ff.items() if valor
        ),
        "Tensões Fase-Neutro": ", ".join(
            f"{fase}: {valor}" for fase, valor in tensoes_fn.items() if valor
        ),
        "Tensões Terra": ", ".join(
            f"{fase}: {valor}" for fase, valor in tensoes_ft.items() if valor
        ),
        "Correntes": ", ".join(
            f"{fase}: {valor}" for fase, valor in correntes.items() if valor
        ),
    }
    return row


def _collect_custos_materiais_row():
    """Collect totals from the "Custos com Materiais" section."""

    row = {
        "Aba": "Custos com Materiais",
        "Total Materiais": st.session_state.get("total_custos_materiais", 0.0),
        "Total Infra-Seca": st.session_state.get("total_infra_seca", 0.0),
        "Total Quadro de Proteção": st.session_state.get(
            "total_quadro_protecao", 0.0
        ),
        "Total Material Adicional": st.session_state.get(
            "total_material_adicional", 0.0
        ),
    }
    return row


def _collect_custo_mao_obra_row():
    """Collect totals from the "Custo Mão de Obra" section."""

    row = {
        "Aba": "Custo Mão de Obra",
        "Total Técnicos": st.session_state.get("total_tecnicos_servico", 0.0),
        "Total Alimentação": st.session_state.get("total_alimentacao_servico", 0.0),
        "Total Serviços Adicionais": st.session_state.get(
            "total_servicos_adicionais", 0.0
        ),
        "Custo Obra Civil": st.session_state.get("custo_obra_civil", 0.0),
        "Custo Infra de Rede": st.session_state.get("custo_infra_rede", 0.0),
        "Custo Andaime": st.session_state.get("custo_andaime", 0.0),
        "Custo Pintura da Vaga": st.session_state.get("custo_pintura_vaga", 0.0),
        "Custo Pintura Eletrodutos": st.session_state.get(
            "custo_pintura_eletrodutos", 0.0
        ),
        "Custo Caminhão Munk": st.session_state.get("custo_caminhao_munk", 0.0),
        "Total Mão de Obra": st.session_state.get("total_custo_mao_obra", 0.0),
    }
    return row


def _collect_calculo_servico_row():
    """Collect the totals calculated in the "Cálculo de serviço" tab."""

    total_materiais = _parse_to_positive_float(
        st.session_state.get("total_custos_materiais", 0.0)
    )
    total_mao_obra = _parse_to_positive_float(
        st.session_state.get("total_custo_mao_obra", 0.0)
    )
    custo_deslocamento = _parse_to_positive_float(
        st.session_state.get("total_custo_deslocamento", 0.0)
    )
    custo_adicional = _parse_to_positive_float(
        st.session_state.get("custo_adicional", 0.0)
    )
    servicos_adicionais = _parse_to_positive_float(
        st.session_state.get("total_servicos_adicionais", 0.0)
    )
    custo_emissao_trt = _parse_to_positive_float(
        st.session_state.get("custo_emissao_trt", 0.0)
    )
    custo_projeto_unifilar = _parse_to_positive_float(
        st.session_state.get("custo_projeto_unifilar", 0.0)
    )

    base_sem_carregador = (
        total_materiais
        + total_mao_obra
        + custo_deslocamento
        + custo_adicional
        + servicos_adicionais
        + custo_emissao_trt
        + custo_projeto_unifilar
    )

    depreciacao = st.session_state.get("depreciacao")
    if depreciacao is None:
        depreciacao = 0.05 * base_sem_carregador

    lucro_percentual = _parse_to_positive_float(
        st.session_state.get("lucro_percentual", 35.0)
    )
    lucro = st.session_state.get("lucro")
    if lucro is None:
        lucro = (lucro_percentual / 100) * (base_sem_carregador + depreciacao)

    imposto_percentual = _parse_to_positive_float(
        st.session_state.get("imposto_percentual", 11.0)
    )
    imposto = st.session_state.get("imposto")
    if imposto is None:
        imposto = (imposto_percentual / 100) * (
            base_sem_carregador + depreciacao + lucro
        )

    total_carregadores = _parse_to_positive_float(
        st.session_state.get("total_carregadores", 0.0)
    )

    total_servico = _parse_to_positive_float(
        st.session_state.get("total_calculo_servico", 0.0)
    )
    total_instalacao_valor = st.session_state.get("total_instalacao_valor")
    if total_instalacao_valor is None:
        total_instalacao_valor = (
            total_servico - (custo_emissao_trt + custo_projeto_unifilar) - total_carregadores
        )

    row = {
        "Aba": "Cálculo de serviço",
        "Total Materiais": total_materiais,
        "Total Mão de Obra": total_mao_obra,
        "Custo Deslocamento": custo_deslocamento,
        "Custo Adicional": custo_adicional,
        "Serviços Adicionais": servicos_adicionais,
        "Custo Emissão TRT": custo_emissao_trt,
        "Custo Projeto Unifilar": custo_projeto_unifilar,
        "Depreciação": depreciacao,
        "Lucro (%)": lucro_percentual,
        "Lucro": lucro,
        "Imposto (%)": imposto_percentual,
        "Imposto": imposto,
        "Total Carregadores": total_carregadores,
        "Base sem Carregador": base_sem_carregador,
        "Total Instalação (valor)": total_instalacao_valor,
        "Total Serviço": total_servico,
    }
    return row


def _collect_orcamento_row():
    """Collect the visible data from the "Orçamento" tab."""

    total_instalacao_formatado = st.session_state.get("total_instalacao", "")
    total_instalacao_valor = st.session_state.get("total_instalacao_valor", 0.0)
    total_carregador_formatado = st.session_state.get("total_carregador", "")
    total_carregador_valor = _parse_to_positive_float(
        st.session_state.get("total_carregadores", 0.0)
    )

    row = {
        "Aba": "Orçamento",
        "Cliente": st.session_state.get("cliente_orcamento", ""),
        "Pronome": st.session_state.get("pronome_orcamento", ""),
        "Descrição dos Serviços": st.session_state.get("descricao_servicos", ""),
        "Tipo de Serviço": st.session_state.get("tipo_servico_orcamento", ""),
        "Tempo Estimado (dias)": st.session_state.get("tempo_estimado_obra", ""),
        "Condições de Pagamento": st.session_state.get("condicoes_pagamento", ""),
        "Potência do Carregador": st.session_state.get(
            "potencia_carregador_orcamento", ""
        ),
        "Tensão do Carregador": st.session_state.get(
            "tensao_carregador_orcamento", ""
        ),
        "Distância total da Infra": st.session_state.get(
            "distancia_total_infra", ""
        ),
        "Total Instalação": total_instalacao_formatado,
        "Total Instalação (valor)": total_instalacao_valor,
        "Total Carregador": total_carregador_formatado,
        "Total Carregador (valor)": total_carregador_valor,
    }
    return row


def _collect_consolidated_rows():
    """Gather the data from all relevant tabs for the consolidated Excel report."""

    rows = []
    for collector in (
        _collect_visita_report_row,
        _collect_resumo_report_row,
        _collect_custos_materiais_row,
        _collect_custo_mao_obra_row,
        _collect_calculo_servico_row,
        _collect_orcamento_row,
    ):
        row = collector()
        if row and any(
            value not in (None, "") for key, value in row.items() if key != "Aba"
        ):
            rows.append(row)
    return rows


ORCAMENTO_SNAPSHOT_KEYS = [
    "total_custos_materiais",
    "total_custo_mao_obra",
    "total_custo_deslocamento",
    "total_calculo_servico",
    "cliente_orcamento",
    "pronome_orcamento",
    "descricao_servicos",
    "tipo_servico_orcamento",
    "tempo_estimado_obra",
    "condicoes_pagamento",
    "distancia_total_infra",
    "total_instalacao",
    "total_carregador",
    "potencia_carregador_orcamento",
    "tensao_carregador_orcamento",
    "ordem_venda",
]


def _get_orcamento_form_snapshot():
    return tuple((key, st.session_state.get(key)) for key in ORCAMENTO_SNAPSHOT_KEYS)


def render_orcamento_tab(tab_orcamento):
    """Renderiza a aba de Orçamento."""
    with tab_orcamento:
        st.markdown(
            """
            <style>
            div[data-testid="stTabPanel"]:nth-of-type(4) {
                background-color: #1e4f79;
                color: white;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.title("🧾 Orçamento")
        st.info("Seção para geração do documento de orçamento.")

        cliente_visita = st.session_state.get("cliente", "")
        if st.session_state.get("cliente_orcamento", "") == "":
            st.session_state["cliente_orcamento"] = cliente_visita

        tipo_servico_visita = st.session_state.get("tipo_servico", "")
        if st.session_state.get("tipo_servico_orcamento", "") == "":
            st.session_state["tipo_servico_orcamento"] = tipo_servico_visita

        col_pronome, col_cliente = st.columns([1, 3])
        with col_pronome:
            st.selectbox(
                "Pronome",
                ["Ao Sr.", "À Sra.", "À"],
                key="pronome_orcamento",
            )
        with col_cliente:
            st.text_input("Nome do Cliente", key="cliente_orcamento")

        if st.session_state.get("descricao_servicos", "") == "":
            st.session_state["descricao_servicos"] = tipo_servico_visita

        if "tempo_estimado_obra" not in st.session_state:
            st.session_state["tempo_estimado_obra"] = 1

        col_desc, col_tempo, col_tipo = st.columns(3)
        with col_desc:
            st.selectbox(
                "Descrição dos Serviços",
                [
                    "",
                    "Instalação",
                    "Manutenção",
                    "Manutenção Preventiva",
                    "Manutenção Corretiva",
                    "Análise de Energia",
                ],
                key="descricao_servicos",
            )
        with col_tempo:
            st.number_input(
                "Tempo estimado (dias)",
                min_value=0,
                step=1,
                key="tempo_estimado_obra",
            )
        with col_tipo:
            st.text_input("Tipo de Serviço", key="tipo_servico_orcamento")

        potencia_visita = st.session_state.get("potencia_carregador", "")
        if potencia_visita == "Outro":
            potencia_visita = f"{st.session_state.get('pot_outro_valor', 0)} kW"
        if st.session_state.get("potencia_carregador_orcamento", "") == "":
            st.session_state["potencia_carregador_orcamento"] = potencia_visita

        # Define a tensão do carregador automaticamente com base na potência
        potencia_str = st.session_state.get("potencia_carregador_orcamento", "")
        potencia_val = 0.0
        match_pot = re.search(r"([\d.,]+)", str(potencia_str))
        if match_pot:
            try:
                potencia_val = float(match_pot.group(1).replace(",", "."))
            except ValueError:
                potencia_val = 0.0
        tensao_val = "220V" if potencia_val <= 7.4 else "380V"
        st.session_state["tensao_carregador_orcamento"] = tensao_val

        distancia_total_infra = sum(
            trecho for _, trecho in st.session_state.get("percursos", [])
        )
        st.session_state["distancia_total_infra"] = f"{distancia_total_infra:g}"

        col_pot, col_tensao, col_dist = st.columns(3)
        with col_pot:
            st.text_input(
                "Potência do Carregador",
                key="potencia_carregador_orcamento",
            )
        with col_tensao:
            st.text_input(
                "Tensão do Carregador",
                key="tensao_carregador_orcamento",
                disabled=True,
            )
        with col_dist:
            st.text_input(
                "Distância total da Infra",
                key="distancia_total_infra",
                disabled=True,
            )

        soma_parcial_custos = st.session_state.get("soma_parcial_custos")
        total_instalacao = st.session_state.get("total_instalacao_calculo_servico")
        if total_instalacao is None:
            soma_parcial_custos = soma_parcial_custos if soma_parcial_custos is not None else 0.0
            total_instalacao = format_currency(soma_parcial_custos)
        st.session_state["total_instalacao"] = total_instalacao
        st.text_input(
            "Total Instalação",
            key="total_instalacao",
            disabled=True,
        )

        total_carregadores = _parse_to_positive_float(
            st.session_state.get("total_carregadores", 0.0)
        )
        st.session_state["total_carregador"] = format_currency(
            total_carregadores
        )
        st.text_input(
            "Total Carregador",
            key="total_carregador",
            disabled=True,
        )

        st.selectbox(
            "Condições de pagamento",
            [
                "50% antecipado e 50% em 15 dias",
                "A Vista antecipado",
                "A Vista ao final do serviço",
                "Wecharge",
            ],
            key="condicoes_pagamento",
        )

        previous_snapshot = st.session_state.get("orcamento_form_snapshot")
        current_snapshot = _get_orcamento_form_snapshot()
        if previous_snapshot is not None and previous_snapshot != current_snapshot:
            st.session_state.pop("orcamento_doc_bytes", None)
            st.session_state.pop("orcamento_file_name", None)
            st.session_state.pop("relatorio_consolidado_bytes", None)
            st.session_state.pop("relatorio_consolidado_file_name", None)

        if st.button("Gerar orçamento"):
            st.session_state.pop("orcamento_doc_bytes", None)
            st.session_state.pop("orcamento_file_name", None)

            buffer = gerar_documento_orcamento()
            ordem_venda = st.session_state.get("ordem_venda", "").strip()
            base_name = "Proposta Técnica e Comercial"
            file_name = (
                f"{base_name} {ordem_venda}.docx" if ordem_venda else f"{base_name}.docx"
            )

            st.session_state["orcamento_doc_bytes"] = buffer.getvalue()
            st.session_state["orcamento_file_name"] = file_name

        doc_bytes = st.session_state.get("orcamento_doc_bytes")
        doc_file_name = st.session_state.get("orcamento_file_name")
        if doc_bytes and doc_file_name:
            st.download_button(
                "📄 Baixar Orçamento",
                data=doc_bytes,
                file_name=doc_file_name,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="orcamento_download_button",
            )

        if st.button("Gerar relatório consolidado"):
            st.session_state.pop("relatorio_consolidado_bytes", None)
            st.session_state.pop("relatorio_consolidado_file_name", None)

            rows = _collect_consolidated_rows()
            if not rows:
                st.warning(
                    "Não há dados suficientes para gerar o relatório consolidado."
                )
            else:
                df_relatorio = pd.DataFrame(rows)
                buffer = io.BytesIO()
                try:
                    df_relatorio.to_excel(buffer, index=False)
                except ImportError:
                    st.error(
                        "Não foi possível gerar o relatório porque a biblioteca "
                        "'openpyxl' não está instalada. Execute `pip install openpyxl` "
                        "e tente novamente."
                    )
                else:
                    buffer.seek(0)
                    ordem_venda = st.session_state.get("ordem_venda", "").strip()
                    base_name = "Relatorio Consolidado"
                    file_name = (
                        f"{base_name} {ordem_venda}.xlsx"
                        if ordem_venda
                        else f"{base_name}.xlsx"
                    )
                    st.session_state["relatorio_consolidado_bytes"] = buffer.getvalue()
                    st.session_state["relatorio_consolidado_file_name"] = file_name

        relatorio_bytes = st.session_state.get("relatorio_consolidado_bytes")
        relatorio_file_name = st.session_state.get("relatorio_consolidado_file_name")
        if relatorio_bytes and relatorio_file_name:
            st.download_button(
                "📊 Baixar Relatório Consolidado",
                data=relatorio_bytes,
                file_name=relatorio_file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="relatorio_consolidado_download_button",
            )

        st.session_state["orcamento_form_snapshot"] = _get_orcamento_form_snapshot()
