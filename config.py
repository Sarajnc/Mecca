"""
config.py
---------
Persiste configurações simples do MECCA (caminho da planilha, nome da aba)
em um arquivo JSON local, para o usuário não ter que reconfigurar toda vez.
"""

import json
import os

CAMINHO_CONFIG = "config_mecca.json"

PADRAO = {
    "arquivo_planilha": "MÓDULO RPF RENAULT 66.xlsx",
    "aba_planilha": "BASE TOTAL",
}


def carregar_config() -> dict:
    if not os.path.exists(CAMINHO_CONFIG):
        return dict(PADRAO)
    try:
        with open(CAMINHO_CONFIG, "r", encoding="utf-8") as f:
            dados = json.load(f)
        cfg = dict(PADRAO)
        cfg.update(dados)
        return cfg
    except Exception:
        return dict(PADRAO)


def salvar_config(cfg: dict) -> None:
    with open(CAMINHO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
