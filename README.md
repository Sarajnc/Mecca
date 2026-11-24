# MECCA — Automação de Peças e Revisões

Sistema desktop desenvolvido em Python para a **Central de Agendamentos da Santa Emília Renault**, com o objetivo de automatizar a consulta de peças de revisão e a **inclusão dos códigos das peças na pré-OS** diretamente no sistema **Apollo** (`GestaoPosVendasClient.exe`).

A ferramenta elimina a digitação manual código por código durante a preparação dos agendamentos, reduzindo falhas operacionais e agilizando o fluxo de atendimento de pós-vendas.

---

## Funcionalidades

* **Painel de Indicadores (Dashboard):** Visão geral em tempo real com total de consultas realizadas, lançamentos concluídos na pré-OS e quantidade acumulada de peças enviadas ao Apollo.
* **Consulta Inteligente por Veículo:** Filtragem automática por **Modelo**, **Motor**, **Ano** (com validação de faixas como `19/23`) e **Quilometragem da Revisão**, incluindo regras específicas de lubrificantes (ex.: motores `1.3` e modelos `Kardian`/`Boreal`).
* **Inclusão Automatizada na Pré-OS (Apollo):** Integração direta via automação de interface (`pywinauto`) executada em segundo plano (*multithreading*) para inserir os códigos e quantidades na pré-OS sem travar a aplicação.
* **Histórico de Operações:** Registro local automático (`historico_mecca.json`) com data, hora, dados do veículo, quantidade de peças e status do lançamento (*Lançado*, *Cancelado* ou *Erro*).
* **Configurações Persistentes:** Tela de ajustes para selecionar o arquivo `.xlsx` e a aba da planilha sem precisar alterar o código-fonte.

---

## Tecnologias Utilizadas

• Python 3.10+ — Linguagem principal
• CustomTkinter — Interface gráfica moderna e responsiva
• Pandas & OpenPyXL — Leitura, tratamento e filtragem da base de peças em Excel
• Pywinauto — Automação de interface Windows para integração com o Apollo

---

## Estrutura do Projeto

```text
Mecca/
├── app.py                # Interface gráfica principal e fluxo de telas
├── backend.py            # Regras de negócio, leitura da planilha e automação Apollo
├── config.py             # Gerenciamento das configurações locais
├── config_mecca.json     # Parâmetros padrão (caminho da planilha e aba)
├── historico.py          # Controle de leitura e gravação do histórico
├── iniciar.bat           # Atalho para abrir o sistema sem janela de console
├── requirements.txt      # Dependências do projeto
└── .gitignore            # Arquivos ignorados (planilhas internas e logs locais)
```

---

## Como Instalar e Executar

### 1. Pré-requisitos
* Sistema operacional **Windows** (necessário para integração com o cliente desktop do Apollo).
* **Python 3.10 ou superior** instalado.
* Sistema **Apollo** (`GestaoPosVendasClient.exe`) aberto na tela de agendamento / pré-OS antes de iniciar o lançamento.

### 2. Clonar o repositório
```bash
git clone https://github.com
cd Mecca
```

### 3. Instalar as dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar a planilha de dados
> **Nota:** Por motivos de confidencialidade corporativa, a planilha oficial de peças não está incluída neste repositório.

1. Inicie a aplicação executando `python app.py` (ou dê um duplo clique no arquivo `.bat`).
2. Acesse a aba **Ajustes** (`⚙`) no menu lateral.
3. Clique em **Procurar...**, selecione a planilha Excel de revisão correspondente e informe o **Nome da aba** (padrão: `BASE TOTAL`).
4. Clique em **Salvar configurações**.

---

## Como Usar

1. **Preencher Dados:** Na aba **Consulta** (`⌕`), informe o **Modelo**, **Motor**, **Ano** e **Revisão (km)** do veículo agendado e clique em **Buscar peças** (ou pressione `Enter`).
2. **Conferir Lista:** Verifique as referências, descrições e quantidades retornadas na tabela.
3. **Incluir na Pré-OS:** Com o Apollo aberto na tela do agendamento, clique em **Confirmar e lançar no Apollo** e acompanhe o progresso no rodapé até a conclusão da inclusão dos códigos.

---

## Contexto e Licença

Projeto desenvolvido para apoiar a rotina operacional da **Central de Agendamentos da Santa Emília Renault**, otimizando a preparação de pré-ordens de serviço (pré-OS) no setor de pós-vendas.
