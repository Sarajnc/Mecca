import threading
import queue
import customtkinter as ctk
from tkinter import filedialog

import backend
import historico
import config

CORES = {
    "bg": "#f6eff3",  # mauve-50  - fundo principal (claro)
    "bg_secundario": "#eddee6",  # mauve-100 - áreas de apoio
    "topbar": "#21121a",         # mauve-900 - barra superior
    "sidebar": "#21121a",        # mauve-900 - menu lateral
    "card": "#21121a",           # mauve-900 - cards principais
    "card_hover": "#2b1722",     # mix 900/800 - hover sutil (sem blocos vinho pesados)
    "border": "#422434",         # mauve-800 - contornos finos
    "divisor": "#dbbdcd",  # mauve-200 - linhas/bordas sobre o fundo claro
    "primary": "#c99cb5",        # mauve-300 - destaque principal (rosa antigo, suave)
    "primary_hover": "#dbbdcd",  # mauve-200 - hover do destaque
    "primary_soft": "#dbbdcd",   # mauve-200 - ícones e detalhes
    "on_primary": "#170d12",     # mauve-950 - texto sobre o destaque
    "muted": "#a88f9c",          # mauve-grafite - texto secundário
    "muted_soft": "#d3bfca",     # mauve-claro - labels / menu
    "accent_bg": "#844869",       # mauve-600 - destaque em texto sobre o fundo claro
    "muted_bg": "#844869",  # mauve-600 - texto secundário sobre o fundo claro
    "input": "#170d12",          # mauve-950 - campos de entrada
    "text": "#21121a",  # mauve-900 - títulos sobre o fundo claro
    "text_dim": "#eddee6",       # mauve-100
    "text_card": "#f6eff3",      # mauve-50  - texto dentro dos cards
    "success": "#1f9d55",  # verde legível no claro e no escuro
    "danger": "#dc2626",  # vermelho legível no claro e no escuro
    "warning": "#fbbf24",
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

FONTE_TITULO = ("Segoe UI Semibold", 26)
FONTE_SUBTITULO = ("Segoe UI", 13)
FONTE_LABEL = ("Segoe UI", 12)
FONTE_TEXTO = ("Segoe UI", 13)
FONTE_BOTAO = ("Segoe UI Semibold", 13)
FONTE_MONO = ("Consolas", 12)


def cor_status(status):
    return {"Lançado": CORES["success"], "Erro": CORES["danger"]}.get(status, CORES["muted"])


class MeccaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MECCA — Automação de Peças")
        self.geometry("1180x760")
        self.minsize(960, 640)

        self.configure(fg_color=CORES["bg"])

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Estado da consulta atual
        self.dados_planilha = None
        self.pecas_encontradas = None
        self.apollo = None
        self.fila_mensagens = queue.Queue()
        self.tela_atual = "inicio"

        self._criar_menu_lateral()
        self._criar_area_principal()

        # Mapeamento das telas
        self.mapa_de_telas = {
            "inicio": self.tela_inicio,
            "consulta": self.tela_consulta,
            "historico": self.tela_historico,
            "configuracoes": self.tela_configuracoes,
        }

        self.mostrar_tela("inicio")

    # ------------------------------------------------------------------- #
    # Menu lateral enxuto (logo uma única vez + ícones com rótulo curto)
    # ------------------------------------------------------------------- #
    def _criar_menu_lateral(self):
        self.menu_lateral = ctk.CTkFrame(self, width=88, corner_radius=0, fg_color=CORES["sidebar"])
        self.menu_lateral.grid(row=0, column=0, sticky="nswe")
        self.menu_lateral.grid_propagate(False)
        self.menu_lateral.grid_columnconfigure(0, weight=1)
        self.menu_lateral.grid_rowconfigure(7, weight=1)

        botao_logo = ctk.CTkButton(
            self.menu_lateral, text="M", width=48, height=48, corner_radius=14,
            font=("Segoe UI Semibold", 22), fg_color=CORES["primary"],
            hover_color=CORES["primary_hover"], text_color=CORES["on_primary"],
            command=lambda: self.mostrar_tela("inicio"))
        botao_logo.grid(row=0, column=0, pady=(22, 6))

        ctk.CTkLabel(self.menu_lateral, text="MECCA", font=("Segoe UI Semibold", 11),
                     text_color=CORES["muted_soft"]).grid(row=1, column=0, pady=(0, 14))

        ctk.CTkFrame(self.menu_lateral, height=1, fg_color=CORES["border"]).grid(
            row=2, column=0, sticky="we", padx=18, pady=(0, 12))

        self.botoes_menu = {}
        itens_menu = [
            ("consulta", "⌕", "Consulta"),
            ("historico", "⏱", "Histórico"),
            ("configuracoes", "⚙", "Ajustes"),
        ]
        for linha, (tela, icone, rotulo) in enumerate(itens_menu, start=3):
            self._criar_item_menu(tela, icone, rotulo, linha)

    def _criar_item_menu(self, tela, icone, rotulo, linha):
        item = ctk.CTkFrame(self.menu_lateral, width=68, height=62, corner_radius=14,
                            fg_color=CORES["sidebar"])
        item.grid(row=linha, column=0, pady=3)
        item.pack_propagate(False)

        rotulo_icone = ctk.CTkLabel(item, text=icone, font=("Segoe UI", 20),
                                    text_color=CORES["muted_soft"], fg_color=CORES["sidebar"])
        rotulo_icone.pack(pady=(8, 0))
        rotulo_texto = ctk.CTkLabel(item, text=rotulo, font=("Segoe UI", 10),
                                    text_color=CORES["muted"], fg_color=CORES["sidebar"])
        rotulo_texto.pack()

        self.botoes_menu[tela] = (item, rotulo_icone, rotulo_texto)

        for elemento in (item, rotulo_icone, rotulo_texto):
            elemento.bind("<Button-1>", lambda evento, destino=tela: self.mostrar_tela(destino))
            elemento.bind("<Enter>", lambda evento, destino=tela: self._hover_item_menu(destino, True))
            elemento.bind("<Leave>", lambda evento, destino=tela: self._hover_item_menu(destino, False))

    def _pintar_item_menu(self, tela, fundo, cor_icone, cor_texto):
        item, rotulo_icone, rotulo_texto = self.botoes_menu[tela]
        item.configure(fg_color=fundo)
        rotulo_icone.configure(fg_color=fundo, text_color=cor_icone)
        rotulo_texto.configure(fg_color=fundo, text_color=cor_texto)

    def _hover_item_menu(self, tela, entrou):
        if tela == self.tela_atual:
            return
        fundo = CORES["card_hover"] if entrou else CORES["sidebar"]
        self._pintar_item_menu(tela, fundo, CORES["muted_soft"], CORES["muted"])

    def _destacar_botao_ativo(self, tela_ativa):
        for tela in self.botoes_menu:
            if tela == tela_ativa:
                self._pintar_item_menu(tela, CORES["primary"], CORES["on_primary"], CORES["on_primary"])
            else:
                self._pintar_item_menu(tela, CORES["sidebar"], CORES["muted_soft"], CORES["muted"])

    # ------------------------------------------------------------------- #
    # Área principal (troca de telas)
    # ------------------------------------------------------------------- #
    def _criar_area_principal(self):
        self.area_principal = ctk.CTkFrame(self, fg_color=CORES["bg"], corner_radius=0)
        self.area_principal.grid(row=0, column=1, sticky="nswe")
        self.area_principal.grid_rowconfigure(0, weight=1)
        self.area_principal.grid_columnconfigure(0, weight=1)

        self.tela_inicio = self._criar_tela_inicio(self.area_principal)
        self.tela_consulta = self._criar_tela_consulta(self.area_principal)
        self.tela_historico = self._criar_tela_historico(self.area_principal)
        self.tela_configuracoes = self._criar_tela_configuracoes(self.area_principal)

        for tela in (
            self.tela_consulta,
            self.tela_historico,
            self.tela_configuracoes,
            self.tela_inicio
        ):
            tela.grid(row=0, column=0, sticky="nswe")

    def mostrar_tela(self, tela):
        self.tela_atual = tela
        self._destacar_botao_ativo(tela)
        self.mapa_de_telas[tela].tkraise()

        if tela == "inicio":
            self._atualizar_painel()
        if tela == "historico":
            self._recarregar_historico()

    # ------------------------------------------------------------------- #
    # Tela: Painel (início)
    # ------------------------------------------------------------------- #
    def _criar_tela_inicio(self, area_pai):
        tela = ctk.CTkFrame(area_pai, fg_color=CORES["bg"])
        tela.grid_columnconfigure(0, weight=1)
        tela.grid_rowconfigure(2, weight=1)

        # Cabeçalho
        cabecalho = ctk.CTkFrame(tela, fg_color="transparent")
        cabecalho.grid(row=0, column=0, sticky="we", padx=36, pady=(30, 10))
        ctk.CTkLabel(cabecalho, text="B E M - V I N D O ( A )", font=("Segoe UI Semibold", 12),
                     text_color=CORES["accent_bg"]).pack(anchor="w")
        ctk.CTkLabel(cabecalho, text="Painel", font=FONTE_TITULO,
                     text_color=CORES["text"]).pack(anchor="w")
        ctk.CTkLabel(cabecalho, text="Visão geral das consultas e lançamentos de peças de revisão.",
                     font=FONTE_SUBTITULO, text_color=CORES["muted_bg"]).pack(anchor="w")

        # Faixa de números
        faixa = ctk.CTkFrame(tela, fg_color=CORES["card"], corner_radius=18,
                             border_width=1, border_color=CORES["border"])
        faixa.grid(row=1, column=0, sticky="we", padx=36, pady=(8, 12))
        for coluna in range(3):
            faixa.grid_columnconfigure(coluna, weight=1, uniform="kpi")

        self.valores_kpi = {}

        def criar_kpi(coluna, chave, rotulo, legenda):
            celula = ctk.CTkFrame(faixa, fg_color="transparent")
            celula.grid(row=0, column=coluna, sticky="nswe", padx=(26, 10), pady=16)
            ctk.CTkLabel(celula, text=rotulo, font=("Segoe UI Semibold", 11),
                         text_color=CORES["muted"]).pack(anchor="w")
            valor = ctk.CTkLabel(celula, text="0", font=("Segoe UI Semibold", 30),
                                 text_color=CORES["text_card"])
            valor.pack(anchor="w")
            ctk.CTkLabel(celula, text=legenda, font=("Segoe UI", 11),
                         text_color=CORES["muted_soft"]).pack(anchor="w")
            self.valores_kpi[chave] = valor
            if coluna > 0:
                ctk.CTkFrame(faixa, width=1, fg_color=CORES["border"]).grid(
                    row=0, column=coluna, sticky="nsw", pady=16)

        criar_kpi(0, "consultas", "CONSULTAS", "registradas no total")
        criar_kpi(1, "lancadas", "LANÇAMENTOS", "concluídos no Apollo")
        criar_kpi(2, "pecas", "PEÇAS LANÇADAS", "enviadas ao Apollo")

        # Corpo: últimas consultas
        corpo = ctk.CTkFrame(tela, fg_color="transparent")
        corpo.grid(row=2, column=0, sticky="nswe", padx=36, pady=(0, 24))
        corpo.grid_columnconfigure(0, weight=1)
        corpo.grid_rowconfigure(0, weight=1)

        # -- Card: últimas consultas
        cartao_recentes = ctk.CTkFrame(corpo, fg_color=CORES["card"], corner_radius=18,
                                       border_width=1, border_color=CORES["border"])
        cartao_recentes.grid(row=0, column=0, sticky="nswe")
        cartao_recentes.grid_columnconfigure(0, weight=1)
        cartao_recentes.grid_rowconfigure(1, weight=1)

        topo_recentes = ctk.CTkFrame(cartao_recentes, fg_color="transparent")
        topo_recentes.grid(row=0, column=0, sticky="we", padx=24, pady=(20, 8))
        ctk.CTkLabel(topo_recentes, text="Últimas consultas", font=("Segoe UI Semibold", 16),
                     text_color=CORES["text_card"]).pack(side="left")
        ctk.CTkButton(topo_recentes, text="Ver tudo  →", font=("Segoe UI", 12), width=90, height=30,
                      corner_radius=15, fg_color="transparent", hover_color=CORES["card_hover"],
                      text_color=CORES["primary_soft"],
                      command=lambda: self.mostrar_tela("historico")).pack(side="right")

        self.lista_recentes = ctk.CTkFrame(cartao_recentes, fg_color="transparent")
        self.lista_recentes.grid(row=1, column=0, sticky="nswe", padx=16, pady=(0, 16))
        self.lista_recentes.grid_columnconfigure(0, weight=1)

        return tela

    def _atualizar_painel(self):
        try:
            registros = historico.carregar_historico()
        except Exception:
            registros = []

        lancados = [r for r in registros if r["status"] == "Lançado"]
        total_pecas = 0
        for registro in lancados:
            try:
                total_pecas += int(registro["qtd_pecas"])
            except (TypeError, ValueError):
                pass

        self.valores_kpi["consultas"].configure(text=str(len(registros)))
        self.valores_kpi["lancadas"].configure(text=str(len(lancados)))
        self.valores_kpi["pecas"].configure(text=str(total_pecas))

        for elemento in self.lista_recentes.winfo_children():
            elemento.destroy()

        if not registros:
            ctk.CTkLabel(self.lista_recentes, text="Nenhuma consulta registrada ainda.",
                         font=FONTE_TEXTO, text_color=CORES["muted"]).grid(row=0, column=0, pady=40)
            return

        for indice, registro in enumerate(registros[:5]):
            fundo = CORES["input"] if indice % 2 == 0 else CORES["card"]
            linha = ctk.CTkFrame(self.lista_recentes, fg_color=fundo, corner_radius=12)
            linha.grid(row=indice, column=0, sticky="we", pady=3)
            linha.grid_columnconfigure(0, weight=1)

            cor = cor_status(registro["status"])
            ctk.CTkFrame(linha, width=3, corner_radius=2, fg_color=cor).place(x=6, rely=0.2, relheight=0.6)

            ctk.CTkLabel(linha, text=f'{registro["modelo"]} · {registro["motor"]}',
                         font=("Segoe UI Semibold", 13), text_color=CORES["text_card"], anchor="w"
                         ).grid(row=0, column=0, sticky="w", padx=(20, 8), pady=(10, 0))
            ctk.CTkLabel(linha,
                         text=f'{registro["ano"]} · {registro["km"]} km · {registro["qtd_pecas"]} peças · {registro["data_hora"]}',
                         font=("Segoe UI", 11), text_color=CORES["muted"], anchor="w"
                         ).grid(row=1, column=0, sticky="w", padx=(20, 8), pady=(0, 10))
            ctk.CTkLabel(linha, text=registro["status"], font=("Segoe UI Semibold", 11),
                         text_color=CORES["on_primary"], fg_color=cor, corner_radius=6,
                         width=88, height=24
                         ).grid(row=0, column=1, rowspan=2, padx=(6, 16), sticky="e")

    # Tela: Nova consulta (fluxo em 3 passos)
    def _criar_tela_consulta(self, area_pai):
        tela = ctk.CTkFrame(area_pai, fg_color=CORES["bg"])
        tela.grid_columnconfigure(0, weight=1)
        tela.grid_rowconfigure(3, weight=1)

        cabecalho = ctk.CTkFrame(tela, fg_color="transparent")
        cabecalho.grid(row=0, column=0, sticky="we", padx=36, pady=(30, 10))
        ctk.CTkLabel(cabecalho, text="Nova consulta", font=FONTE_TITULO,
                     text_color=CORES["text"]).pack(anchor="w")
        ctk.CTkLabel(cabecalho, text="Preencha os dados do veículo para buscar as peças da revisão.",
                     font=FONTE_SUBTITULO, text_color=CORES["muted_bg"]).pack(anchor="w")

        # Indicador de passos: Veículo → Peças → Lançar
        barra_passos = self._criar_indicador_passos(tela)
        barra_passos.grid(row=1, column=0, sticky="we", padx=36, pady=(2, 12))

        # Cartão do formulário
        formulario = ctk.CTkFrame(tela, fg_color=CORES["card"], corner_radius=18,
                                  border_width=1, border_color=CORES["border"])
        formulario.grid(row=2, column=0, sticky="we", padx=36, pady=(0, 10))
        for coluna in range(4):
            formulario.grid_columnconfigure(coluna, weight=1)

        ctk.CTkLabel(formulario, text="DADOS DO VEÍCULO", font=("Segoe UI Semibold", 11),
                     text_color=CORES["muted"]).grid(row=0, column=0, columnspan=4, sticky="w",
                                                     padx=18, pady=(16, 0))

        self.campo_modelo = self._criar_campo_formulario(formulario, "Modelo", 1, 0)
        self.campo_motor = self._criar_campo_formulario(formulario, "Motor", 1, 1)
        self.campo_ano = self._criar_campo_formulario(formulario, "Ano", 1, 2, largura=100)
        self.campo_km = self._criar_campo_formulario(formulario, "Revisão (km)", 1, 3, largura=130)

        for campo in(self.campo_modelo, self.campo_motor, self.campo_ano, self.campo_km):
            campo.bind("<Return>", lambda evento: self.buscar_pecas())

        self.botao_buscar = ctk.CTkButton(
            formulario, text="Buscar peças", font=FONTE_BOTAO, height=40,
            fg_color=CORES["primary"], hover_color=CORES["primary_hover"],
            text_color=CORES["on_primary"], corner_radius=20, command=self.buscar_pecas,
        )
        self.botao_buscar.grid(row=2, column=3, sticky="e", padx=18, pady=(0, 18))

        self.texto_erro = ctk.CTkLabel(formulario, text="", font=FONTE_LABEL,
                                        text_color=CORES["danger"], anchor="w")
        self.texto_erro.grid(row=2, column=0, columnspan=3, sticky="w", padx=18, pady=(0, 18))

        # Cartão de resultados (resumo + tabela + painel de lançamento)
        area_resultados = ctk.CTkFrame(tela, fg_color=CORES["card"], corner_radius=18,
                                        border_width=1, border_color=CORES["border"])
        area_resultados.grid(row=3, column=0, sticky="nswe", padx=36, pady=(0, 10))
        area_resultados.grid_rowconfigure(2, weight=1)
        area_resultados.grid_columnconfigure(0, weight=1)

        topo_resultados = ctk.CTkFrame(area_resultados, fg_color="transparent")
        topo_resultados.grid(row=0, column=0, sticky="we", padx=18, pady=(16, 6))
        topo_resultados.grid_columnconfigure(0, weight=1)

        bloco_titulo = ctk.CTkFrame(topo_resultados, fg_color="transparent")
        bloco_titulo.grid(row=0, column=0, sticky="w")
        self.titulo_resultados = ctk.CTkLabel(
            bloco_titulo, text="Peças encontradas", font=("Segoe UI Semibold", 15),
            text_color=CORES["text_card"])
        self.titulo_resultados.pack(anchor="w")
        self.resumo_veiculo = ctk.CTkLabel(
            bloco_titulo, text="Nenhum veículo consultado ainda.", font=FONTE_LABEL,
            text_color=CORES["muted"])
        self.resumo_veiculo.pack(anchor="w")

        self.chip_total = ctk.CTkLabel(
            topo_resultados, text="0 peças", font=("Segoe UI Semibold", 11),
            text_color=CORES["primary_soft"], fg_color=CORES["card_hover"],
            corner_radius=13, width=80, height=26)
        self.chip_total.grid(row=0, column=1, sticky="e")

        # Cabeçalho da tabela
        cabecalho_tabela = ctk.CTkFrame(area_resultados, fg_color=CORES["input"], corner_radius=8, height=30)
        cabecalho_tabela.grid(row=1, column=0, sticky="we", padx=(14, 30), pady=(2, 4))
        cabecalho_tabela.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(cabecalho_tabela, text="REFERÊNCIA", font=("Segoe UI Semibold", 10),
                     text_color=CORES["muted"], width=110, anchor="w"
                     ).grid(row=0, column=0, padx=(14, 6), pady=6, sticky="w")
        ctk.CTkLabel(cabecalho_tabela, text="DESCRIÇÃO", font=("Segoe UI Semibold", 10),
                     text_color=CORES["muted"], anchor="w"
                     ).grid(row=0, column=1, pady=6, sticky="w")
        ctk.CTkLabel(cabecalho_tabela, text="QTD.", font=("Segoe UI Semibold", 10),
                     text_color=CORES["muted"], width=70, anchor="e"
                     ).grid(row=0, column=2, padx=(6, 14), pady=6, sticky="e")

        self.lista_resultados = ctk.CTkScrollableFrame(area_resultados, fg_color="transparent",
                                                  scrollbar_button_color=CORES["border"],
                                                  scrollbar_button_hover_color=CORES["primary"])
        self.lista_resultados.grid(row=2, column=0, sticky="nswe", padx=10, pady=(0, 10))
        self.lista_resultados.grid_columnconfigure(0, weight=1)

        self.mensagem_resultados = ctk.CTkLabel(
            self.lista_resultados,
            text="As peças da revisão vão aparecer aqui depois da busca.",
            font=FONTE_TEXTO, text_color=CORES["muted"])
        self.mensagem_resultados.grid(row=0, column=0, pady=30)

        # Rodapé de confirmação
        self.rodape_confirmacao = ctk.CTkFrame(tela, fg_color="transparent")
        self.rodape_confirmacao.grid(row=4, column=0, sticky="we", padx=36, pady=(0, 12))
        self.rodape_confirmacao.grid_columnconfigure(0, weight=1)

        self.texto_status_lancamento = ctk.CTkLabel(
            self.rodape_confirmacao, text="", font=FONTE_LABEL, text_color=CORES["muted_bg"])
        self.texto_status_lancamento.grid(row=0, column=0, sticky="w")

        self.botoes_confirmacao = ctk.CTkFrame(self.rodape_confirmacao, fg_color="transparent")
        self.botoes_confirmacao.grid(row=0, column=1, sticky="e")

        self.botao_cancelar = ctk.CTkButton(
            self.botoes_confirmacao, text="Cancelar", font=FONTE_BOTAO, height=38, width=110,
            fg_color="transparent", hover_color=CORES["card_hover"],
            text_color=CORES["muted_bg"], border_width=1, border_color=CORES["divisor"],
            corner_radius=20, command=self.cancelar_consulta,
        )
        self.botao_confirmar = ctk.CTkButton(
            self.botoes_confirmacao, text="Confirmar e lançar no Apollo", font=FONTE_BOTAO,
            height=38, fg_color=CORES["success"], hover_color="#22c55e",
            text_color="#0c0c18", corner_radius=20, command=self.confirmar_lancamento,
        )
        self._esconder_botoes_confirmacao()
        self._definir_passo(1)

        return tela

    # ---- indicador de passos (Veículo → Peças → Lançar) ---- #
    def _criar_indicador_passos(self, pai):
        barra = ctk.CTkFrame(pai, fg_color="transparent")
        self.passos = []
        self.conectores = []
        for indice, nome in enumerate(("Veículo", "Peças", "Lançar")):
            if indice > 0:
                conector = ctk.CTkFrame(barra, width=60, height=2, corner_radius=1,
                                        fg_color=CORES["divisor"])
                conector.pack(side="left", padx=12)
                self.conectores.append(conector)
            bolinha = ctk.CTkLabel(barra, text=str(indice + 1), width=30, height=30, corner_radius=15,
                                   font=("Segoe UI Semibold", 13), fg_color=CORES["bg_secundario"],
                                   text_color=CORES["muted_bg"])
            bolinha.pack(side="left")
            rotulo = ctk.CTkLabel(barra, text=nome, font=FONTE_BOTAO, text_color=CORES["muted_bg"])
            rotulo.pack(side="left", padx=(8, 0))
            self.passos.append((bolinha, rotulo))
        return barra

    def _definir_passo(self, atual):
        # atual: 1 = Veículo, 2 = Peças, 3 = Lançar, 4 = tudo concluído
        for numero, (bolinha, rotulo) in enumerate(self.passos, start=1):
            if numero < atual:
                bolinha.configure(text="✓", fg_color=CORES["primary"], text_color=CORES["on_primary"])
                rotulo.configure(text_color=CORES["muted_bg"])
            elif numero == atual:
                bolinha.configure(text=str(numero), fg_color=CORES["accent_bg"], text_color=CORES["text_card"])
                rotulo.configure(text_color=CORES["text"])
            else:
                bolinha.configure(text=str(numero), fg_color=CORES["bg_secundario"], text_color=CORES["muted_bg"])
                rotulo.configure(text_color=CORES["muted_bg"])
        for numero, conector in enumerate(self.conectores, start=1):
            conector.configure(fg_color=CORES["primary"] if atual > numero else CORES["divisor"])

    # ---- resumo da consulta ---- #
    def _atualizar_resumo(self, veiculo=None, quantidade=0):
        self.resumo_veiculo.configure(text=veiculo or "Nenhum veículo consultado ainda.")
        self.chip_total.configure(text="1 peça" if quantidade == 1 else f"{quantidade} peças")

    def _criar_campo_formulario(self, area_pai, rotulo, linha, coluna, largura=None):
        area_campo = ctk.CTkFrame(area_pai, fg_color="transparent")
        area_campo.grid(row=linha, column=coluna, sticky="we", padx=18, pady=(18, 6))
        ctk.CTkLabel(area_campo, text=rotulo, font=FONTE_LABEL,
                     text_color=CORES["muted_soft"]).pack(anchor="w", pady=(0, 4))
        campo = ctk.CTkEntry(
            area_campo, font=FONTE_TEXTO, height=36, corner_radius=8,
            fg_color=CORES["input"], border_color=CORES["border"], border_width=1,
            text_color=CORES["text_card"], width=largura or 160,
        )
        campo.pack(fill="x")
        return campo

    def _esconder_botoes_confirmacao(self):
        self.botao_cancelar.pack_forget()
        self.botao_confirmar.pack_forget()

    def _mostrar_botoes_confirmacao(self):
        self.botao_cancelar.pack(side="left", padx=(0, 8))
        self.botao_confirmar.pack(side="left")

    def _limpar_resultados(self):
        for elemento in self.lista_resultados.winfo_children():
            elemento.destroy()

    def _criar_linha_peca(self, pai, indice, peca):
        cor_fundo = CORES["input"] if indice % 2 == 0 else CORES["card"]
        linha = ctk.CTkFrame(pai, fg_color=cor_fundo, corner_radius=8)
        linha.grid(row=indice, column=0, sticky="we", pady=3, padx=2)
        linha.grid_columnconfigure(1, weight=1)
        ctk.CTkFrame(linha, width=3, corner_radius=2, fg_color=CORES["primary"]).place(x=5, rely=0.2, relheight=0.6)

        ctk.CTkLabel(linha, text=str(peca["Referência"]), font=FONTE_MONO,
                     text_color=CORES["primary_soft"], width=110, anchor="w"
                     ).grid(row=0, column=0, padx=(14, 6), pady=10, sticky="w")
        ctk.CTkLabel(linha, text=str(peca["Descrição"]), font=FONTE_TEXTO,
                     text_color=CORES["text_card"], anchor="w", justify="left"
                     ).grid(row=0, column=1, sticky="w", pady=10)
        ctk.CTkLabel(linha, text=f'Qtd: {peca["Quantidade"]}', font=FONTE_LABEL,
                     text_color=CORES["muted_soft"], width=70, anchor="e"
                     ).grid(row=0, column=2, padx=(6, 14), pady=10, sticky="e")

    # ---- ações da tela de consulta ---- #
    def buscar_pecas(self):
        self._limpar_dados_temporarios()
        self.pecas_encontradas = None

        self.texto_erro.configure(text="")
        self._esconder_botoes_confirmacao()
        self.texto_status_lancamento.configure(text="")
        self._definir_passo(1)
        self._atualizar_resumo()

        modelo = self.campo_modelo.get().strip()
        motor = self.campo_motor.get().strip()
        texto_ano = self.campo_ano.get().strip()
        texto_km = self.campo_km.get().strip()

        if not modelo or not motor or not texto_ano or not texto_km:
            self.texto_erro.configure(text="Preencha todos os campos antes de buscar.")
            return

        try:
            ano = int(texto_ano)
            km = int(texto_km)
        except ValueError:
            self.texto_erro.configure(text="Ano e revisão (km) precisam ser números.")
            return

        self.botao_buscar.configure(state="disabled", text="Buscando...")
        self.update_idletasks()

        try:
            configuracoes = config.carregar_config()
            self.dados_planilha = backend.carregar_planilha(
                configuracoes["arquivo_planilha"], configuracoes["aba_planilha"])
            self.pecas_encontradas = backend.buscar_pecas_revisao(
                self.dados_planilha, modelo, motor, ano, km)
        except backend.ErroAutomacao as erro:
            self.texto_erro.configure(text=str(erro))
            self.pecas_encontradas = None
        finally:
            self.botao_buscar.configure(state="normal", text="Buscar peças")

        self._limpar_resultados()
        if self.pecas_encontradas is not None and not self.pecas_encontradas.empty:
            self.titulo_resultados.configure(
                text=f"Peças encontradas ({len(self.pecas_encontradas)})")
            for indice, (_, peca) in enumerate(self.pecas_encontradas.iterrows()):
                self._criar_linha_peca(self.lista_resultados, indice, peca)
            self._mostrar_botoes_confirmacao()
            self._dados_consulta_atual = (modelo, motor, ano, km)
            self._atualizar_resumo(f"{modelo} · {motor} · {ano} · {km} km", len(self.pecas_encontradas))
            self._definir_passo(2)
        else:
            self.titulo_resultados.configure(text="Peças encontradas")
            ctk.CTkLabel(self.lista_resultados,
                         text="Nenhuma peça encontrada para esses dados.",
                         font=FONTE_TEXTO, text_color=CORES["muted"]).grid(row=0, column=0, pady=30)

    def cancelar_consulta(self):
        modelo, motor, ano, km = getattr(self, "_dados_consulta_atual", ("", "", 0, 0))
        historico.salvar_registro(modelo, motor, ano, km,
                                   len(self.pecas_encontradas) if self.pecas_encontradas is not None else 0,
                                   "Cancelado")
        self.pecas_encontradas = None
        self._limpar_dados_temporarios()

        self._limpar_resultados()
        self.titulo_resultados.configure(text="Peças encontradas")
        ctk.CTkLabel(self.lista_resultados,
                     text="As peças da revisão vão aparecer aqui depois da busca.",
                     font=FONTE_TEXTO, text_color=CORES["muted"]).grid(row=0, column=0, pady=30)
        self._esconder_botoes_confirmacao()
        self.texto_status_lancamento.configure(text="Consulta cancelada.", text_color=CORES["muted_bg"])
        self._definir_passo(1)
        self._atualizar_resumo()

    def confirmar_lancamento(self):
        if self.pecas_encontradas is None or self.pecas_encontradas.empty:
            return
        self.botao_confirmar.configure(state="disabled")
        self.botao_cancelar.configure(state="disabled")
        self.texto_status_lancamento.configure(
            text="Conectando ao Apollo...", text_color=CORES["muted_bg"])

        self._definir_passo(3)

        tarefa_lancamento = threading.Thread(target=self._lancar_pecas_em_segundo_plano, daemon=True)
        tarefa_lancamento.start()
        self.after(100, self._verificar_fila_mensagens)

    def _lancar_pecas_em_segundo_plano(self):
        modelo, motor, ano, km = self._dados_consulta_atual
        try:
            apollo = backend.conectar_apollo()
            self.fila_mensagens.put(("status", "Conectado ao Apollo. Iniciando lançamento..."))
            backend.lancar_pecas_no_apollo(
                apollo, self.pecas_encontradas,
                callback_status=lambda mensagem: self.fila_mensagens.put(("status", mensagem)))
            historico.salvar_registro(modelo, motor, ano, km, len(self.pecas_encontradas), "Lançado")
            self.fila_mensagens.put(("fim_ok", "Peças lançadas no Apollo com sucesso!"))
        except backend.ErroAutomacao as erro:
            historico.salvar_registro(modelo, motor, ano, km, len(self.pecas_encontradas), "Erro")
            self.fila_mensagens.put(("fim_erro", str(erro)))
        except Exception as erro:
            historico.salvar_registro(modelo, motor, ano, km, len(self.pecas_encontradas), "Erro")
            self.fila_mensagens.put(("fim_erro", f"Erro inesperado: {erro}"))

    def _verificar_fila_mensagens(self):
        try:
            while True:
                tipo, mensagem = self.fila_mensagens.get_nowait()
                if tipo == "status":
                    self.texto_status_lancamento.configure(text=mensagem, text_color=CORES["muted_bg"])
                elif tipo == "fim_ok":
                    self.texto_status_lancamento.configure(text=mensagem, text_color=CORES["success"])
                    self._definir_passo(4)
                    self.botao_confirmar.configure(state="normal")
                    self.botao_cancelar.configure(state="normal")
                    self._esconder_botoes_confirmacao()

                    self.pecas_encontradas = None
                    self._limpar_dados_temporarios()
                    return
        
                elif tipo == "fim_erro":
                    self.texto_status_lancamento.configure(text=mensagem, text_color=CORES["danger"])
                    self.botao_confirmar.configure(state="normal")
                    self.botao_cancelar.configure(state="normal")

                    self.pecas_encontradas = None
                    self._limpar_dados_temporarios()
                    return
        except queue.Empty:
            pass
        self.after(100, self._verificar_fila_mensagens)

    # ------------------------------------------------------------------- #
    # Tela: Histórico
    # ------------------------------------------------------------------- #
    def _criar_tela_historico(self, area_pai):
        tela = ctk.CTkFrame(area_pai, fg_color=CORES["bg"])
        tela.grid_columnconfigure(0, weight=1)
        tela.grid_rowconfigure(2, weight=1)

        cabecalho = ctk.CTkFrame(tela, fg_color="transparent")
        cabecalho.grid(row=0, column=0, sticky="we", padx=36, pady=(30, 10))
        ctk.CTkLabel(cabecalho, text="Histórico", font=FONTE_TITULO,
                     text_color=CORES["text"]).pack(side="left")

        botao_atualizar = ctk.CTkButton(
            cabecalho, text="Atualizar", font=FONTE_BOTAO, height=34, width=110,
            fg_color=CORES["card"], hover_color=CORES["card_hover"],
            border_width=1, border_color=CORES["border"], text_color=CORES["muted_soft"],
            corner_radius=20, command=self._recarregar_historico,
        )
        botao_atualizar.pack(side="right")

        self.lista_historico = ctk.CTkScrollableFrame(tela, fg_color="transparent",
                                                scrollbar_button_color=CORES["divisor"],
                                                scrollbar_button_hover_color=CORES["primary"])
        self.lista_historico.grid(row=2, column=0, sticky="nswe", padx=36, pady=(4, 24))
        self.lista_historico.grid_columnconfigure(0, weight=1)

        return tela

    def _recarregar_historico(self):
        for elemento in self.lista_historico.winfo_children():
            elemento.destroy()

        registros = historico.carregar_historico()
        if not registros:
            ctk.CTkLabel(self.lista_historico, text="Nenhuma consulta registrada ainda.",
                         font=FONTE_TEXTO, text_color=CORES["muted_bg"]).grid(row=0, column=0, pady=30)
            return

        cores_status = {
            "Lançado": CORES["success"],
            "Cancelado": CORES["muted"],
            "Erro": CORES["danger"],
        }

        for indice, registro in enumerate(registros):
            linha = ctk.CTkFrame(self.lista_historico, fg_color=CORES["card"], corner_radius=14,
                                  border_width=1, border_color=CORES["border"])
            linha.grid(row=indice, column=0, sticky="we", pady=4, padx=2)
            linha.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(linha, text=registro["data_hora"], font=FONTE_LABEL,
                         text_color=CORES["muted"], width=110, anchor="w"
                         ).grid(row=0, column=0, padx=(16, 6), pady=12, sticky="w")

            texto_veiculo = f'{registro["modelo"]} · {registro["motor"]} · {registro["ano"]} · {registro["km"]} km'
            ctk.CTkLabel(linha, text=texto_veiculo, font=FONTE_TEXTO,
                         text_color=CORES["text_card"], anchor="w"
                         ).grid(row=0, column=1, sticky="w", pady=12)

            ctk.CTkLabel(linha, text=f'{registro["qtd_pecas"]} peças', font=FONTE_LABEL,
                         text_color=CORES["muted_soft"], anchor="e"
                         ).grid(row=0, column=2, padx=(6, 12), pady=12, sticky="e")

            indicador_status_historico = ctk.CTkLabel(
                linha, text=registro["status"], font=("Segoe UI Semibold", 11),
                text_color=CORES["on_primary"], fg_color=cores_status.get(registro["status"], CORES["muted"]),
                corner_radius=6, width=88, height=24)
            indicador_status_historico.grid(row=0, column=3, padx=(6, 16), pady=12, sticky="e")
            ctk.CTkFrame(linha, width=3, corner_radius=2,
                         fg_color=cores_status.get(registro["status"], CORES["muted"])
                         ).place(x=6, rely=0.2, relheight=0.6)

    # ------------------------------------------------------------------- #
    # Tela: Configurações
    # ------------------------------------------------------------------- #
    def _criar_tela_configuracoes(self, area_pai):
        tela = ctk.CTkFrame(area_pai, fg_color=CORES["bg"])
        tela.grid_columnconfigure(0, weight=1)

        cabecalho = ctk.CTkFrame(tela, fg_color="transparent")
        cabecalho.grid(row=0, column=0, sticky="we", padx=36, pady=(30, 10))
        ctk.CTkLabel(cabecalho, text="Configurações", font=FONTE_TITULO,
                     text_color=CORES["text"]).pack(anchor="w")
        ctk.CTkLabel(cabecalho, text="Ajuste o arquivo de planilha usado nas buscas.",
                     font=FONTE_SUBTITULO, text_color=CORES["muted_bg"]).pack(anchor="w")

        painel_configuracoes = ctk.CTkFrame(tela, fg_color=CORES["card"], corner_radius=18,
                             border_width=1, border_color=CORES["border"])
        painel_configuracoes.grid(row=1, column=0, sticky="we", padx=36, pady=10)
        painel_configuracoes.grid_columnconfigure(0, weight=1)

        configuracoes = config.carregar_config()

        ctk.CTkLabel(painel_configuracoes, text="Arquivo da planilha (.xlsx)", font=FONTE_LABEL,
                     text_color=CORES["muted_soft"]).grid(row=0, column=0, sticky="w", padx=18, pady=(18, 4))
        linha_arquivo = ctk.CTkFrame(painel_configuracoes, fg_color="transparent")
        linha_arquivo.grid(row=1, column=0, sticky="we", padx=18)
        linha_arquivo.grid_columnconfigure(0, weight=1)

        self.campo_arquivo = ctk.CTkEntry(
            linha_arquivo, font=FONTE_TEXTO, height=36, corner_radius=8,
            fg_color=CORES["input"], border_color=CORES["border"], border_width=1,
            text_color=CORES["text_card"])
        self.campo_arquivo.insert(0, configuracoes["arquivo_planilha"])
        self.campo_arquivo.grid(row=0, column=0, sticky="we", padx=(0, 8))

        ctk.CTkButton(linha_arquivo, text="Procurar...", font=FONTE_BOTAO, height=36, width=110,
                      fg_color=CORES["card_hover"], hover_color=CORES["border"],
                      text_color=CORES["text_card"], corner_radius=20,
                      command=self._escolher_arquivo).grid(row=0, column=1)

        ctk.CTkLabel(painel_configuracoes, text="Nome da aba", font=FONTE_LABEL,
                     text_color=CORES["muted_soft"]).grid(row=2, column=0, sticky="w", padx=18, pady=(16, 4))
        self.campo_aba = ctk.CTkEntry(
            painel_configuracoes, font=FONTE_TEXTO, height=36, corner_radius=8, width=260,
            fg_color=CORES["input"], border_color=CORES["border"], border_width=1,
            text_color=CORES["text_card"])
        self.campo_aba.insert(0, configuracoes["aba_planilha"])
        self.campo_aba.grid(row=3, column=0, sticky="w", padx=18)

        linha_botoes = ctk.CTkFrame(painel_configuracoes, fg_color="transparent")
        linha_botoes.grid(row=4, column=0, sticky="we", padx=18, pady=18)

        ctk.CTkButton(linha_botoes, text="Salvar configurações", font=FONTE_BOTAO, height=38,
                      fg_color=CORES["primary"], hover_color=CORES["primary_hover"],
                      text_color=CORES["on_primary"], corner_radius=20,
                      command=self._salvar_configuracoes).pack(side="left", padx=(0, 8))

        self.mensagem_configuracao = ctk.CTkLabel(painel_configuracoes, text="", font=FONTE_LABEL, text_color=CORES["muted"])
        self.mensagem_configuracao.grid(row=5, column=0, sticky="w", padx=18, pady=(0, 16))

        return tela

    def _escolher_arquivo(self):
        caminho = filedialog.askopenfilename(filetypes=[("Planilhas Excel", "*.xlsx *.xls")])
        if caminho:
            self.campo_arquivo.delete(0, "end")
            self.campo_arquivo.insert(0, caminho)

    def _salvar_configuracoes(self):
        config.salvar_config({
            "arquivo_planilha": self.campo_arquivo.get().strip(),
            "aba_planilha": self.campo_aba.get().strip(),
        })
        self.mensagem_configuracao.configure(text="Configurações salvas.", text_color=CORES["success"])

    def _limpar_dados_temporarios(self):
        self.dados_planilha = None

if __name__ == "__main__":
    app = MeccaApp()
    app.mainloop()