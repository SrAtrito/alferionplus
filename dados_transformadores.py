"""Dados padrão e utilitários para transformadores."""
from __future__ import annotations

from copy import deepcopy
from typing import Dict, List

_TRANSFORMADORES_PADRAO: List[Dict[str, float]] = [
    {
        "Produto": "Auto Trafo 220/380V 25KVA IP21 (Magnetix)",
        "Preço": 2900.00,
    },
    {
        "Produto": "Auto Trafo 220/380V 25KVA IP54 (Magnetix)",
        "Preço": 3330.00,
    },
    {
        "Produto": "Auto Trafo 220/380V 30KVA IP21 (Magnetix)",
        "Preço": 3025.00,
    },
    {
        "Produto": "Auto Trafo 220/380V 30KVA IP54 (Magnetix)",
        "Preço": 3450.00,
    },
    {
        "Produto": "Auto Trafo 220/380V 50KVA IP21 (Magnetix)",
        "Preço": 5150.00,
    },
    {
        "Produto": "Auto Trafo 220/380V 50KVA IP54 (Magnetix)",
        "Preço": 4600.00,
    },
    {
        "Produto": "Potência Isolador  220/380V 25KVA IP21 (Magnetix)",
        "Preço": 5400.00,
    },
    {
        "Produto": "Potência Isolador  220/380V 30KVA IP21 (Magnetix)",
        "Preço": 5900.00,
    },
    {
        "Produto": "Potência Isolador  220/380V 50KVA IP21 (Magnetix)",
        "Preço": 8470.00,
    },
]


def obter_transformadores_padrao() -> List[Dict[str, float]]:
    """Retorna uma cópia da lista padrão de transformadores."""
    return deepcopy(_TRANSFORMADORES_PADRAO)


def obter_produtos_transformadores_padrao() -> List[str]:
    """Retorna a lista padrão de nomes de produtos de transformadores."""
    return [item["Produto"] for item in _TRANSFORMADORES_PADRAO]
