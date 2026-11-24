"""
historico.py
------------
Armazena e recupera o histórico de consultas do MECCA em um arquivo JSON local.
"""

import json
import os
from datetime import datetime

CAMINHO_HISTORICO = "historico_mecca.json"
LIMITE_REGISTROS = 200


def carregar_historico() -> list:
    if not os.path.exists(CAMINHO_HISTORICO):
        return []
    try:
        with open(CAMINHO_HISTORICO, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def salvar_registro(modelo: str, motor: str, ano: int, km: int,
                     qtd_pecas: int, status: str) -> None:
    """
    status esperado: 'Lançado', 'Cancelado' ou 'Erro'
    """
    historico = carregar_historico()
    registro = {
        "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "modelo": modelo,
        "motor": motor,
        "ano": ano,
        "km": km,
        "qtd_pecas": qtd_pecas,
        "status": status,
    }
    historico.insert(0, registro)
    historico = historico[:LIMITE_REGISTROS]

    with open(CAMINHO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)
