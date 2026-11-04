# 🎸 Empório da Música — Intelligent Customer Support Agent

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/Framework-LangChain-green.svg)](https://www.langchain.com/)
[![Google Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-orange.svg)](https://ai.google.dev/)
[![Tests](https://img.shields.io/badge/Tests-75%20Passed-brightgreen.svg)](tests/)

> **Language / Idioma:** [English](#-english) | [Português](#-português)

---

## 🇺🇸 English

### 📖 About the Project
Autonomous customer support agent designed for **Empório da Música**, a traditional musical instrument store located in Campo Grande, MS, Brazil.

Built with Google Gemini (`gemini-3.5-flash-lite`), LangChain, and a lightweight local vector search engine (RAG), the agent provides accurate, polite, and grounded customer service using a warm regional tone of voice.

### ✨ Key Capabilities
- **Real-Time Catalog Inquiries (Decision A):** Queries product inventory, specifications, and active promotions using strict structured function calling with pandas.
- **Semantic Policy RAG (Decision B):** Extracts and searches the official store policies manual (`políticas_da_loja.pdf`) using `gemini-embedding-001` and cosine similarity in numpy.
- **Secure Order Status Lookup:** Strict identity validation requiring order number, email, and phone number of the cardholder before displaying sensitive shipment data.
- **Multi-Turn Persistent Memory:** Thread-based SQLite conversation history (`storage/memory.sqlite3`).
- **Guardrails (Decision C):** Cordially declines out-of-scope inquiries and reminds customers that the store does not sell standalone accessories (cables, strings, cases).

---

### 🏛️ Architecture Overview

```
[ User (CLI / Gradio Web) ]
             │
             ▼
   [ EmporioAgent (Gemini 3.5 Flash Lite) ]
             │
   ┌─────────┼─────────────────────────┐
   │         │                         │
[Decision A] [Decision B]          [Decision C]
(Structured Data) (Semantic RAG)   (Out-of-Scope Guardrail)
   │         │                         │
   ▼         ▼                         ▼
Tools CSV   PolicyRetriever         Polite Refusal
(Pandas)    (gemini-embedding-001   (Regional Persona)
            + Cosine Numpy)
   │         │
   └─────────┴─────────┐
                       ▼
       [ SQLiteConversationMemory ]
            (storage/memory.sqlite3)
```

---

### 📁 Repository Structure

```
Artefact-Data-Engineer-Technical-Test/
├── assets/
│   ├── business rules/políticas_da_loja.pdf  # Official PDF policy document
│   └── csv/                                  # Customers, products, orders, categories, promotions
├── src/emporio_da_musica/
│   ├── agent/             # Persona, system prompt, ReAct agent loop
│   ├── app/               # CLI and Gradio Web interfaces
│   ├── data/              # CSV loaders, normalization utils, type schemas
│   ├── memory/            # SQLite multi-turn persistence
│   ├── rag/               # PDF parser, semantic chunking, numpy vector store
│   ├── tools/             # Function calling tool registry
│   └── config.py          # Unified path and model settings
├── storage/               # Runtime artifacts (vector index and SQLite database)
├── tests/                 # 75 unit and integration tests (100% offline & mock-tested)
├── pyproject.toml
└── requirements.txt
```

---

### 🚀 Getting Started

#### 1. Setup Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

#### 2. Environment Variables
Create a `.env` file in the root directory:
```ini
GOOGLE_API_KEY=your_api_key_here
EMPORIO_CHAT_MODEL=gemini-3.5-flash-lite
EMPORIO_EMBEDDING_MODEL=gemini-embedding-001
```

#### 3. Running the Interfaces

- **Web Interface (Gradio):**
  ```powershell
  python -m emporio_da_musica.app.web
  ```
  Open `http://127.0.0.1:7860` in your web browser.

- **Terminal Interface (CLI):**
  ```powershell
  python -m emporio_da_musica.app.cli
  ```

#### 4. Running the Test Suite
```powershell
pytest -v
```

---
---

## 🇧🇷 Português

### 📖 Sobre o Projeto
Agente de atendimento conversacional autônomo desenvolvido para a **Empório da Música**, loja especializada em instrumentos musicais situada em Campo Grande/MS.

Construído utilizando o ecossistema Google Gemini (`gemini-3.5-flash-lite`), LangChain e um motor de busca semântica vetorial local (RAG), o agente fornece respostas precisas, cordiais e fundamentadas com leve sotaque regional sul-mato-grossense.

### ✨ Funcionalidades Principais
- **Consulta de Catálogo em Tempo Real (Decisão A):** Consulta produtos, preços, especificações técnicas e promoções ativas via Function Calling estruturado com pandas.
- **RAG de Políticas da Loja (Decisão B):** Segmenta e recupera regras do manual oficial em PDF (`políticas_da_loja.pdf`) via `gemini-embedding-001` e similaridade de cosseno em numpy.
- **Consulta Segura de Pedidos:** Validação estrita de identidade exigindo número do pedido, e-mail e telefone do titular antes de exibir dados sensíveis ou rastreio.
- **Memória Persistente por Sessão:** Histórico de conversação preservado em SQLite (`storage/memory.sqlite3`) indexado por `thread_id`.
- **Guardrails Rígidos (Decisão C):** Recusa educadamente perguntas fora de contexto e orienta que a loja não comercializa acessórios avulsos (cabos, palhetas, encordoamentos).

---

### 🏛️ Arquitetura do Sistema

```
[ Usuário (CLI / Gradio Web) ]
             │
             ▼
   [ EmporioAgent (Gemini 3.5 Flash Lite) ]
             │
   ┌─────────┼─────────────────────────┐
   │         │                         │
[Decisão A] [Decisão B]            [Decisão C]
(Dados Tabulares) (RAG Semântico)  (Guardrail Fora de Escopo)
   │         │                         │
   ▼         ▼                         ▼
Tools CSV   PolicyRetriever         Recusa educada
(Pandas)    (gemini-embedding-001   (Persona Regional)
            + Cosseno Numpy)
   │         │
   └─────────┴─────────┐
                       ▼
       [ SQLiteConversationMemory ]
            (storage/memory.sqlite3)
```

---

### 📁 Estrutura do Repositório

```
Artefact-Data-Engineer-Technical-Test/
├── assets/
│   ├── business rules/políticas_da_loja.pdf  # Manual oficial de políticas
│   └── csv/                                  # Clientes, produtos, pedidos, categorias, promoções
├── src/emporio_da_musica/
│   ├── agent/             # Persona, system prompt, loop do agente ReAct
│   ├── app/               # Interfaces de usuário (CLI e Gradio Web)
│   ├── data/              # Carga dos CSVs, utilitários de texto, schemas
│   ├── memory/            # Persistência multi-sessão em SQLite
│   ├── rag/               # Extrator de PDF, segmentação, índice vetorial numpy
│   ├── tools/             # Registro de ferramentas (Function Calling)
│   └── config.py          # Centralização de caminhos e modelos
├── storage/               # Artefatos gerados em runtime (vetores e SQLite)
├── tests/                 # 75 testes unitários e de integração (100% offline & mockados)
├── pyproject.toml
└── requirements.txt
```

---

### 🚀 Como Executar

#### 1. Configurar Ambiente Virtual
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

#### 2. Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto:
```ini
GOOGLE_API_KEY=sua_chave_aqui
EMPORIO_CHAT_MODEL=gemini-3.5-flash-lite
EMPORIO_EMBEDDING_MODEL=gemini-embedding-001
```

#### 3. Iniciando as Interfaces

- **Interface Web (Gradio):**
  ```powershell
  python -m emporio_da_musica.app.web
  ```
  Acesse `http://127.0.0.1:7860` no seu navegador.

- **Interface de Terminal (CLI):**
  ```powershell
  python -m emporio_da_musica.app.cli
  ```

#### 4. Executando a Suíte de Testes
```powershell
pytest -v
```
