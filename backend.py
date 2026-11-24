"""
backend.py
----------
Lógica de negócio da automação MECCA: leitura da planilha de peças,
filtragem por modelo/motor/ano/revisão e lançamento no Apollo.

Este módulo não depende de interface gráfica — ele apenas processa dados
e levanta exceções amigáveis (ErroAutomacao) para a camada visual exibir.
"""

import re
import time
import pandas as pd
from pywinauto.application import Application

ARQUIVO_PADRAO = "MÓDULO RPF RENAULT 66.xlsx"
ABA_PADRAO = "BASE TOTAL"


class ErroAutomacao(Exception):
    """Erro amigável, com mensagem pronta para ser exibida ao usuário."""
    pass


# --------------------------------------------------------------------------- #
# Planilha
# --------------------------------------------------------------------------- #

def ano_no_intervalo(texto_intervalo: str, ano_alvo: int) -> bool:
    """Verifica se `ano_alvo` está dentro de um intervalo tipo '19/23'."""
    try:
        anos_encontrados = re.findall(r"\d+", texto_intervalo)
        if len(anos_encontrados) >= 2:
            ano_inicio = int("20" + anos_encontrados[0])
            ano_fim = int("20" + anos_encontrados[-1])
            return ano_inicio <= ano_alvo <= ano_fim
    except Exception:
        return False
    return False


def carregar_planilha(caminho_arquivo: str = ARQUIVO_PADRAO, aba: str = ABA_PADRAO) -> pd.DataFrame:
    """Carrega a planilha de peças. Levanta ErroAutomacao em caso de falha."""
    try:
        return pd.read_excel(caminho_arquivo, sheet_name=aba)
    except FileNotFoundError:
        raise ErroAutomacao(f"Não encontrei o arquivo '{caminho_arquivo}' nesta pasta.")
    except Exception as e:
        raise ErroAutomacao(f"Não consegui abrir a planilha: {e}")


def buscar_pecas_revisao(tabela: pd.DataFrame, modelo: str, motor: str,
                          ano_alvo: int, km: int) -> pd.DataFrame:
    """Filtra a tabela e devolve as peças da revisão pedida."""
    filtrado = tabela[
        (tabela["Modelo"].str.strip().str.lower() == modelo.strip().lower()) &
        (tabela["Motor"].str.contains(motor, case=False, na=False, regex=False)) &
        (tabela["Operação"] == km) &
        (tabela["Tipo Operação"].str.strip().str.lower() == "revisão")
    ]

    if filtrado.empty:
        raise ErroAutomacao(
            f"Não achei nenhuma peça para Modelo='{modelo}', Motor='{motor}', "
            f"Revisão={km} km. Confira se está escrito igual à planilha."
        )

    linhas_validas = filtrado[
        filtrado["ANO"].apply(lambda x: ano_no_intervalo(str(x), ano_alvo))
    ]

    linhas_validas = linhas_validas[
        linhas_validas["Especie"].str.strip().str.lower() == "peça"
    ]

    if linhas_validas.empty:
        anos_disponiveis = list(filtrado["ANO"].unique())
        raise ErroAutomacao(
            f"Achei peças para esse modelo/motor/revisão, mas nenhuma bate "
            f"com o ano {ano_alvo}. Intervalos disponíveis: {anos_disponiveis}"
        )

    resultado = linhas_validas[["Referência", "Descrição", "Quantidade", "Especie"]].copy()
    resultado = resultado.drop_duplicates(subset=["Referência", "Descrição"])

    motor_13 = "1.3" in str(motor)
    boreal = modelo.strip().lower() == "boreal"
    kardian = modelo.strip().lower() == "kardian"
    filtro_lubrificante = resultado["Descrição"].str.contains(
        "Lubrificante Renault 5W40", case=False, na=False
    )

    if motor_13 and not boreal:
        resultado.loc[filtro_lubrificante, "Referência"] = "7711943755"
        resultado.loc[filtro_lubrificante, "Quantidade"] = 5
    elif kardian:
        resultado.loc[filtro_lubrificante, "Referência"] = "7711943755"
        resultado.loc[filtro_lubrificante, "Quantidade"] = 4

    return resultado.reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Apollo
# --------------------------------------------------------------------------- #

def conectar_apollo():
    """Conecta ao processo do Apollo já aberto. Levanta ErroAutomacao se falhar."""
    try:
        return Application(backend="uia").connect(path="GestaoPosVendasClient.exe")
    except Exception as e:
        raise ErroAutomacao(f"Não consegui conectar ao Apollo: {e}")


def lancar_pecas_no_apollo(app, pecas: pd.DataFrame, callback_status=None):
    """
    Lança cada peça no Apollo.
    callback_status(str) é chamado a cada etapa, para a GUI atualizar o status
    (pode ser None se ninguém quiser acompanhar o progresso).
    """
    def status(msg):
        if callback_status:
            callback_status(msg)

    janela = app.window(class_name="TfrmMntAgendaOficina")
    time.sleep(1)

    try:
        aba_pecas = janela.child_window(title="Peças e Serviços", control_type="TabItem")
        aba_pecas.click_input()
    except Exception:
        pass

    status("Aguardando tela de seleção de peças...")
    time.sleep(2)

    janela_selecao = app.window(title="Seleção de Peças")

    total = len(pecas)
    for i, (_, linha) in enumerate(pecas.iterrows(), start=1):
        codigo_peca = str(linha["Referência"]).strip()
        qtd_peca = str(linha["Quantidade"]).strip().replace(".", ",")

        status(f"Lançando peça {i}/{total}: {codigo_peca} (Qtd: {qtd_peca})")

        try:
            janela_selecao.set_focus()
            time.sleep(0.3)

            janela_selecao.type_keys(codigo_peca)
            time.sleep(0.5)

            janela_selecao.type_keys("{ENTER}")
            time.sleep(2)

            janela_selecao.type_keys("{ENTER}")
            time.sleep(0.8)

            janela_selecao.type_keys("{ENTER}")
            time.sleep(1)

        except Exception:
            try:
                janela_qtd = app.window(title_re="Quantidade")
                if janela_qtd.exists(timeout=1):
                    janela_qtd.set_focus()
                    janela_qtd.type_keys("^a{BACKSPACE}")
                    janela_qtd.type_keys(qtd_peca)
                    time.sleep(0.3)
                    janela_qtd.type_keys("{ENTER}")
                    time.sleep(0.5)
            except Exception:
                pass

            time.sleep(0.5)

    status("Processo de lançamento finalizado com sucesso!")
