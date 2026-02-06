"""Tabelas de bitolas de cabos por distância e potência.

Este módulo disponibiliza os dados usados na aba "Tabelas Elétricas".
Inclui a tabela para as fases e a tabela de seção dos fios neutro e terra.
"""

import pandas as pd
from io import StringIO

# Tabela para as fases
CSV_TABELA = """
Distância (m);1,9kW;3,7kW;7,4kW;2x7,4;11,0kW;22,0kW;44,0kW
0 metros;4mm;4mm;10mm;16mm;6mm;10mm;25mm
41 metros;4mm;4mm;10mm;16mm;6mm;10mm;25mm
42 metros;4mm;6mm;10mm;16mm;6mm;10mm;25mm
43 metros;4mm;6mm;10mm;25mm;6mm;10mm;25mm
55 metros;4mm;6mm;10mm;25mm;6mm;10mm;25mm
56 metros;4mm;6mm;16mm;25mm;6mm;10mm;25mm
63 metros;4mm;6mm;16mm;25mm;6mm;10mm;25mm
64 metros;4mm;10mm;16mm;25mm;6mm;10mm;25mm
67 metros;4mm;10mm;16mm;25mm;6mm;10mm;25mm
68 metros;4mm;10mm;16mm;35mm;6mm;10mm;25mm
83 metros;4mm;10mm;16mm;35mm;6mm;10mm;25mm
84 metros;6mm;10mm;16mm;35mm;6mm;10mm;25mm
86 metros;6mm;10mm;16mm;35mm;6mm;10mm;25mm
87 metros;6mm;10mm;25mm;35mm;6mm;10mm;25mm
91 metros;6mm;10mm;25mm;35mm;6mm;10mm;25mm
95 metros;6mm;10mm;25mm;35mm;6mm;10mm;25mm
96 metros;6mm;10mm;25mm;50mm;6mm;10mm;25mm
110 metros;6mm;10mm;25mm;50mm;6mm;10mm;25mm
111 metros;6mm;16mm;25mm;50mm;6mm;10mm;25mm
115 metros;6mm;16mm;25mm;50mm;6mm;10mm;25mm
116 metros;6mm;16mm;25mm;50mm;6mm;16mm;25mm
124 metros;6mm;16mm;25mm;50mm;6mm;16mm;25mm
125 metros;10mm;16mm;25mm;50mm;6mm;16mm;25mm
133 metros;10mm;16mm;25mm;50mm;6mm;16mm;25mm
134 metros;10mm;16mm;25mm;50mm;10mm;16mm;25mm
135 metros;10mm;16mm;25mm;50mm;10mm;16mm;25mm
136 metros;10mm;16mm;35mm;50mm;10mm;16mm;25mm
137 metros;10mm;16mm;35mm;70mm;10mm;16mm;25mm
140 metros;10mm;16mm;35mm;70mm;10mm;16mm;25mm
141 metros;10mm;16mm;35mm;70mm;10mm;16mm;35mm
150 metros;10mm;16mm;35mm;70mm;10mm;16mm;35mm
"""

# Tabela para os fios neutro e terra
CSV_TABELA_NEUTRO_TERRA = """
Distância (m);1,9kW;3,7kW;7,4kW;2x7,4;11,0kW;22,0kW;44,0kW
0 metros;4mm;4mm;10mm;16mm;6mm;10mm;16mm
41 metros;4mm;4mm;10mm;16mm;6mm;10mm;16mm
42 metros;4mm;6mm;10mm;16mm;6mm;10mm;16mm
43 metros;4mm;6mm;10mm;16mm;6mm;10mm;16mm
55 metros;4mm;6mm;10mm;16mm;6mm;10mm;16mm
56 metros;4mm;6mm;16mm;16mm;6mm;10mm;16mm
63 metros;4mm;6mm;16mm;16mm;6mm;10mm;16mm
64 metros;4mm;10mm;16mm;16mm;6mm;10mm;16mm
67 metros;4mm;10mm;16mm;16mm;6mm;10mm;16mm
68 metros;4mm;10mm;16mm;25mm;6mm;10mm;16mm
83 metros;4mm;10mm;16mm;25mm;6mm;10mm;16mm
84 metros;6mm;10mm;16mm;25mm;6mm;10mm;16mm
86 metros;6mm;10mm;16mm;25mm;6mm;10mm;16mm
87 metros;6mm;10mm;16mm;25mm;6mm;10mm;16mm
91 metros;6mm;10mm;16mm;25mm;6mm;10mm;16mm
95 metros;6mm;10mm;16mm;25mm;6mm;10mm;16mm
96 metros;6mm;10mm;16mm;35mm;6mm;10mm;16mm
110 metros;6mm;10mm;16mm;35mm;6mm;10mm;16mm
111 metros;6mm;16mm;16mm;35mm;6mm;10mm;16mm
115 metros;6mm;16mm;16mm;35mm;6mm;10mm;16mm
116 metros;6mm;16mm;16mm;35mm;6mm;16mm;16mm
124 metros;6mm;16mm;16mm;35mm;6mm;16mm;16mm
125 metros;10mm;16mm;16mm;35mm;6mm;16mm;16mm
133 metros;10mm;16mm;16mm;35mm;6mm;16mm;16mm
134 metros;10mm;16mm;16mm;35mm;10mm;16mm;16mm
135 metros;10mm;16mm;16mm;35mm;10mm;16mm;16mm
136 metros;10mm;16mm;25mm;35mm;10mm;16mm;16mm
137 metros;10mm;16mm;25mm;50mm;10mm;16mm;16mm
140 metros;10mm;16mm;25mm;50mm;10mm;16mm;16mm
141 metros;10mm;16mm;25mm;50mm;10mm;16mm;25mm
150 metros;10mm;16mm;25mm;50mm;10mm;16mm;25mm
"""

# Tabela de cabos isolados em PVC flexicom antichama 450/750 V 70°C - Classe 4 ou 5
CSV_TABELA_CABO_ISOLADO_PVC = """Nº1;(Cabo Isolado PVC) Flexicom Antichama 450/750 V 70°C - Classe 4 ou 5;;;
Cabo (mm²);Quantidade de Cabos;Diâmetro Externo (mm);Área do Cabo (mm²);Área Ocupável Condutores
1,5;;2,9;6,61;0,00
2,5;;3,5;9,62;0,00
4,0;;4,0;12,57;0,00
6,0;;4,6;16,62;0,00
10,0;;6,0;28,27;0,00
16,0;;6,8;36,32;0,00
25,0;;8,8;60,82;0,00
35,0;;10,2;81,71;0,00
50,0;;12,3;118,82;0,00
70,0;;14,0;153,94;0,00
95,0;;16,0;201,06;0,00
120,0;;17,8;248,85;0,00
150,0;;19,8;307,91;0,00
185,0;;22,0;380,13;0,00
240,0;;24,6;475,29;0,00
300,0;;27,8;606,99;0,00
400,0;;32,2;814,33;0,00
500,0;;35,8;1006,60;0,00
"""

# Tabela de cabos unipolares HEPR GTEPROM Flex 90°C antichama 0,6/1kV - Classe 5
CSV_TABELA_CABO_UNIPOLAR_HEPR = (
    """Nº6;(Cabo Unipolar HEPR) GTEPROM Flex 90°C Antichama 0,6/1kV - Classe 5;;;
Cabo (mm²);Quantidade de Cabos;Diâmetro Externo (mm);Área do Cabo (mm²);Área Ocupável Condutores
1,5;;4,7;17,35;0,00
2,5;;5,1;20,43;0,00
4,0;;5,7;25,52;0,00
6,0;;6,2;30,19;0,00
10,0;;7,5;44,18;0,00
16,0;;8,6;58,09;0,00
25,0;;10,5;86,59;0,00
35,0;;11,5;103,87;0,00
50,0;;13,8;149,57;0,00
70,0;;15,4;186,27;0,00
95,0;;17,0;226,98;0,00
120,0;;19,0;283,53;0,00
150,0;;21,2;352,99;0,00
185,0;;23,4;430,05;0,00
240,0;;26,4;547,39;0,00
300,0;;29,8;697,46;0,00
400,0;;33,5;881,41;0,00
500,0;;38,0;1134,11;0,00
"""
)

# Tabela de eletrodutos
CSV_TABELA_ELETRODUTOS = """Eletrodutos;;;
Eletroduto (Pol);Diâmetro (mm);Área Total (mm²);Área Ocupável 40% (mm²)
½”;16,4;211,24;84,50
¾”;21,3;356,33;141,36
1”;27,5;593,96;237,58
1 ¼”;36,1;1023,54;409,42
1 ½”;41,4;1346,14;538,46
2”;52,8;2189,56;875,83
2 ½”;67,1;3536,18;1414,47
3”;79,6;4976,41;1990,56
4”;103,1;8348,48;3339,39
"""

def carregar_tabela(csv: str) -> pd.DataFrame:
    """Carrega uma tabela de bitolas como DataFrame.

    As colunas numéricas são convertidas para valores inteiros,
    removendo os sufixos de unidade.
    """
    df = pd.read_csv(StringIO(csv), sep=";")
    df["Distância (m)"] = df["Distância (m)"].str.replace(" metros", "").astype(int)
    for col in df.columns[1:]:
        df[col] = df[col].str.replace("mm", "").astype(int)
    return df

# DataFrames prontos para uso imediato
TABELA_BITOLAS = carregar_tabela(CSV_TABELA)
TABELA_NEUTRO_TERRA = carregar_tabela(CSV_TABELA_NEUTRO_TERRA)
TABELA_CABO_ISOLADO_PVC = pd.read_csv(
    StringIO(CSV_TABELA_CABO_ISOLADO_PVC), sep=";", decimal=",", skiprows=1
)
TABELA_CABO_UNIPOLAR_HEPR = pd.read_csv(
    StringIO(CSV_TABELA_CABO_UNIPOLAR_HEPR), sep=";", decimal=",", skiprows=1
)
TABELA_ELETRODUTOS = pd.read_csv(
    StringIO(CSV_TABELA_ELETRODUTOS), sep=";", decimal=",", skiprows=1
)

__all__ = [
    "carregar_tabela",
    "TABELA_BITOLAS",
    "TABELA_NEUTRO_TERRA",
    "TABELA_CABO_ISOLADO_PVC",
    "TABELA_CABO_UNIPOLAR_HEPR",
    "TABELA_ELETRODUTOS",
]

