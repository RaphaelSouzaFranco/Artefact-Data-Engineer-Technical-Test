# Empório da Música — Intelligent Customer Support Agent

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/Framework-LangChain-green.svg)](https://www.langchain.com/)
[![Google Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-orange.svg)](https://ai.google.dev/)
[![Tests](https://img.shields.io/badge/Tests-78%20Passed-brightgreen.svg)](tests/)

> **Language / Idioma:** [English](#english) | [Português](#português)

---

## English

### About the Project
Autonomous customer support agent designed for **Empório da Música**, a traditional musical instrument store located in Campo Grande, MS, Brazil.

Built with Google Gemini (`gemini-3.5-flash-lite`), LangChain, and a lightweight local vector search engine (RAG), the agent provides accurate, polite, and grounded customer service using a warm regional tone of voice.

### Key Capabilities
- **Real-Time Catalog Inquiries (Decision A):** Queries product inventory, specifications, and active promotions using strict structured function calling with pandas.
- **Semantic Policy RAG (Decision B):** Extracts and searches the official store policies manual (`políticas_da_loja.pdf`) using `gemini-embedding-001` and cosine similarity in numpy.
- **Secure Order Status Lookup:** Strict identity validation requiring order number, email, and phone number of the cardholder before displaying sensitive shipment data.
- **Multi-Turn Persistent Memory:** Thread-based SQLite conversation history (`storage/memory.sqlite3`).
- **Guardrails (Decision C):** Cordially declines out-of-scope inquiries and reminds customers that the store does not sell standalone accessories (cables, strings, cases).

---

### Architecture & Technical Decisions (Rationale)

```
[ User (CLI / Web HTML5/CSS3) ]
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

#### 1. Agentic Framework & Orchestration: LangChain
- **Decision:** Use LangChain (`langchain-core` + `langchain-google-genai`) with native Gemini Tool Calling.
- **Rationale:** Standardizes tool contracts with `@tool`, handles argument serialization/deserialization into Pydantic models automatically, and cleanly decouples prompt templates, tool execution loops, and message schemas (`HumanMessage`, `AIMessage`, `ToolMessage`).

#### 2. Model Selection: Gemini 3.5 Flash Lite & Gemini Embedding 001
- **Decision:** Chat: `gemini-3.5-flash-lite` | Embeddings: `gemini-embedding-001`.
- **Rationale:** 
  - `gemini-3.5-flash-lite` delivers sub-second TTFT (Time to First Token) and low inference latency, ideal for real-time customer service, with native tool-calling reliability.
  - `gemini-embedding-001` provides 3072-dimensional semantic representations, ensuring high precision retrieval over Portuguese institutional guidelines.

#### 3. Retrieval Architecture (RAG): Section-Aware Chunking + Numpy Cosine Index
- **Decision:** Chunk the store manual by logical sections (Sections 1 through 10) and compute cosine similarity using vectorized `numpy` stored on disk (`chunks.json` + `embeddings.npy`).
- **Rationale:** 
  - Fixed-size token chunking often fractures vital business clauses (e.g. splitting 7-day withdrawal rights from refund conditions). Section-based chunking preserves complete contextual integrity.
  - Standalone vector databases (such as ChromaDB, Pinecone, or FAISS) introduce heavy binary dependencies, compilation hurdles on Python 3.14 on Windows, or recurring cloud costs. For an 8-page document (11 chunks), pure `numpy` cosine similarity executes in sub-millisecond speeds with zero infra footprint.

#### 4. Prompting Strategy & Persona Grounding
- **Decision:** Explicit Three-Way Rationale Router (Decisions A, B, and C) + Regional Persona Constraints.
- **Rationale:**
  - Prevents hallucination by requiring function calling for dynamic CSV entities and RAG for policy inquiries.
  - Regional grounding ("Campo Grande/MS", warm, courteous tone) enhances customer trust and engagement.
  - Strict guardrail explicitly forbids hallucinating stock or promising discounts from expired promotions.

#### 5. Data Privacy & Customer Verification (Option A Security Model)
- **Decision:** Mandate both email AND phone number matching the order's customer ID before exposing order progress, tracking codes, or item details.
- **Rationale:**
  - `customers.csv` does not provide CPF numbers. Unauthenticated order lookup allows brute-force enumeration of order IDs. Requiring two independent factors completely closes unauthorized data exposure.
  - Ambiguities (such as customers sharing names or duplicate emails) are reliably disambiguated by matching both email and phone digits.

---

### Repository Structure

```
Artefact-Data-Engineer-Technical-Test/
├── assets/
│   ├── business rules/políticas_da_loja.pdf  # Official PDF policy document
│   └── csv/                                  # Customers, products, orders, categories, promotions
├── src/emporio_da_musica/
│   ├── agent/             # Persona, system prompt, ReAct agent loop
│   ├── app/
│   │   ├── server.py      # FastAPI REST server & static file host
│   │   ├── cli.py         # Terminal CLI chat interface
│   │   └── static/        # Modern HTML5/CSS3/JS Web App (clean minimalist design)
│   │       ├── index.html
│   │       ├── styles.css
│   │       └── app.js
│   ├── data/              # CSV loaders, normalization utils, type schemas
│   ├── memory/            # SQLite multi-turn persistence
│   ├── rag/               # PDF parser, semantic chunking, numpy vector store
│   ├── tools/             # Function calling tool registry
│   └── config.py          # Unified path and model settings
├── storage/               # Runtime artifacts (vector index and SQLite database)
├── tests/                 # 78 unit and integration tests (100% offline & mock-tested)
├── pyproject.toml
└── requirements.txt
```

---

### Getting Started

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

- **Web Application (FastAPI + HTML5/CSS3 UI):**
  ```powershell
  # If virtual environment is activated:
  python -m uvicorn emporio_da_musica.app.server:app --reload --port 8000

  # Or directly using the virtual environment path:
  .\.venv\Scripts\python.exe -m uvicorn emporio_da_musica.app.server:app --reload --port 8000
  ```
  Open `http://localhost:8000` in your web browser.

- **Terminal Interface (CLI):**
  ```powershell
  python -m emporio_da_musica.app.cli
  # or: .\.venv\Scripts\python.exe -m emporio_da_musica.app.cli
  ```

#### 4. Running the Test Suite
```powershell
pytest -v
```

---

### Future Roadmap & Engineering Enhancements

The current architecture provides a robust, decoupled foundation. Key technical enhancements identified for production scaling include:

1. **Semantic Query Caching & Cost Optimization:**
   - Integrate a local Redis or SQLite-based embedding cache for incoming user queries, skipping LLM calls for repeated common FAQs (e.g., store hours, location).
2. **Observability, Tracing & Quality Evaluation:**
   - Instrument the agent with OpenTelemetry / LangSmith to trace token usage, tool latency, and retrieval score distribution per session.
   - Implement an automated LLM-as-a-judge evaluation pipeline (Ragas / G-Eval) evaluating faithfulness, answer relevancy, and guardrail compliance.
3. **Database Migration to Real-Time OLTP:**
   - Replace in-memory pandas CSV loads with a relational database (PostgreSQL with SQLAlchemy/asyncpg) featuring database-level transactions, ACID constraints, and row-level locking for inventory management.
4. **Hybrid Search (BM25 + Dense Vectors):**
   - Combine dense vector retrieval (`gemini-embedding-001`) with sparse keyword matching (BM25 / Reciprocal Rank Fusion) for exact SKU, serial number, and policy section lookups.
5. **Streaming Response Support:**
   - Implement token streaming in `agent.py` and connect it with WebSockets/Server-Sent Events (SSE) in FastAPI to lower perceived latency on longer multi-turn answers.
6. **Containerization & Deployment:**
   - Provide a production-ready multi-stage `Dockerfile` and `docker-compose.yml` including health checks and non-root execution profiles.

---
---

## Português

### Sobre o Projeto
Agente de atendimento conversacional autônomo desenvolvido para a **Empório da Música**, loja especializada em instrumentos musicais situada em Campo Grande/MS.

Construído utilizando o ecossistema Google Gemini (`gemini-3.5-flash-lite`), LangChain e um motor de busca semântica vetorial local (RAG), o agente fornece respostas precisas, cordiais e fundamentadas com leve sotaque regional sul-mato-grossense.

### Funcionalidades Principais
- **Consulta de Catálogo em Tempo Real (Decisão A):** Consulta produtos, preços, especificações técnicas e promoções ativas via Function Calling estruturado com pandas.
- **RAG de Políticas da Loja (Decisão B):** Segmenta e recupera regras do manual oficial em PDF (`políticas_da_loja.pdf`) via `gemini-embedding-001` e similaridade de cosseno em numpy.
- **Consulta Segura de Pedidos:** Validação estrita de identidade exigindo número do pedido, e-mail e telefone do titular antes de exibir dados sensíveis ou rastreio.
- **Memória Persistente por Sessão:** Histórico de conversação preservado em SQLite (`storage/memory.sqlite3`) indexado por `thread_id`.
- **Guardrails Rígidos (Decisão C):** Recusa educadamente perguntas fora de contexto e orienta que a loja não comercializa acessórios avulsos (cabos, palhetas, encordoamentos).

---

### Arquitetura e Decisões Técnicas (Justificativas)

```
[ Usuário (CLI / Web HTML5/CSS3) ]
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

#### 1. Orquestração e Framework: LangChain
- **Decisão:** Adoção do LangChain (`langchain-core` e `langchain-google-genai`) com Function Calling nativo.
- **Justificativa:** Padroniza as ferramentas via `@tool` com validação estrita de esquemas em Pydantic, isola a manipulação de mensagens (`HumanMessage`, `AIMessage`, `ToolMessage`) e facilita a substituição transparente de modelos e componentes sem acoplar a lógica de negócio à API crua do provedor.

#### 2. Escolha dos Modelos: Gemini 3.5 Flash Lite & Gemini Embedding 001
- **Decisão:** Modelo conversacional: `gemini-3.5-flash-lite` | Embeddings: `gemini-embedding-001`.
- **Justificativa:** 
  - O `gemini-3.5-flash-lite` apresenta tempo até o primeiro token (TTFT) extremamente reduzido e alta confiabilidade na chamada de ferramentas, ideal para interfaces conversacionais interativas sem lentidão perceptível.
  - O `gemini-embedding-001` gera representações densas de 3072 dimensões, capturando nuances jurídicas e operacionais do documento em Português com alta acurácia.

#### 3. Arquitetura de Recuperação (RAG): Segmentação por Seções + Vetores em Numpy
- **Decisão:** Divisão semântica baseada nas seções do manual (Seções 1 a 10) e cálculo de similaridade de cosseno com `numpy` persistido em disco (`chunks.json` + `embeddings.npy`).
- **Justificativa:**
  - O chunking puramente por número fixo de caracteres ou tokens fragmenta cláusulas de negócio sensíveis (ex.: separar a regra de 7 dias de arrependimento da condição de embalagem). A segmentação por seções preserva o contexto normativo completo.
  - Bancos vetoriais dedicados (como ChromaDB ou Pinecone) trariam complexidade desnecessária, dependências binárias externas com atritos no Python 3.14 em ambiente Windows ou custo de infraestrutura. Para o manual de 8 páginas (11 chunks), uma matriz `numpy` opera com latência sub-milissegundo e pegada zero de infraestrutura.

#### 4. Estratégia de Prompting e Guardrails
- **Decisão:** Roteador triplo explícito (Decisões A, B e C) aliado a persona regionalizada e restrições rígidas.
- **Justificativa:**
  - Reduz drasticamente alucinações ao forçar a invocação de ferramentas tabulares para dados dinâmicos e do RAG para regras institucionais.
  - A persona sul-mato-grossense (acolhedora, atenciosa e musical) humaniza a experiência e alinha-se ao perfil da loja em Campo Grande/MS.
  - Guardrail explícito impede respostas sobre temas alheios (culinária, fofoca, código) e veda a venda inventada de acessórios avulsos.

#### 5. Modelo de Segurança e Identificação (Opção A)
- **Decisão:** Exigir validação combinada de **E-mail E Telefone** do titular cadastrado para liberar informações do pedido.
- **Justificativa:**
  - Como o CSV original de clientes não possui CPF, uma consulta livre apenas pelo ID do pedido permitiria raspagem maliciosa de dados de entrega e nomes.
  - A exigência de dois fatores independentes combinada à resposta padronizada e opaca em caso de erro neutraliza ataques de enumeração ou desambigua homônimos.

---

### Estrutura do Repositório

```
Artefact-Data-Engineer-Technical-Test/
├── assets/
│   ├── business rules/políticas_da_loja.pdf  # Manual oficial de políticas
│   └── csv/                                  # Clientes, produtos, pedidos, categorias, promoções
├── src/emporio_da_musica/
│   ├── agent/             # Persona, system prompt, loop do agente ReAct
│   ├── app/
│   │   ├── server.py      # Servidor FastAPI REST e entrega de arquivos estáticos
│   │   ├── cli.py         # Interface de linha de comando no terminal
│   │   └── static/        # Aplicação Web HTML5/CSS3/JS (design clean e minimalista)
│   │       ├── index.html
│   │       ├── styles.css
│   │       └── app.js
│   ├── data/              # Carga dos CSVs, utilitários de texto, schemas
│   ├── memory/            # Persistência multi-sessão em SQLite
│   ├── rag/               # Extrator de PDF, segmentação, índice vetorial numpy
│   ├── tools/             # Registro de ferramentas (Function Calling)
│   └── config.py          # Centralização de caminhos e modelos
├── storage/               # Artefatos gerados em runtime (vetores e SQLite)
├── tests/                 # 78 testes unitários e de integração (100% offline & mockados)
├── pyproject.toml
└── requirements.txt
```

---

### Como Executar

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

- **Aplicação Web (Servidor FastAPI + UI HTML5/CSS3):**
  ```powershell
  # Com o ambiente virtual ativado:
  python -m uvicorn emporio_da_musica.app.server:app --reload --port 8000

  # Ou diretamente pelo caminho do ambiente virtual:
  .\.venv\Scripts\python.exe -m uvicorn emporio_da_musica.app.server:app --reload --port 8000
  ```
  Acesse `http://localhost:8000` no seu navegador.

- **Interface de Terminal (CLI):**
  ```powershell
  python -m emporio_da_musica.app.cli
  # ou: .\.venv\Scripts\python.exe -m emporio_da_musica.app.cli
  ```

#### 4. Executando a Suíte de Testes
```powershell
pytest -v
```

---

### Roadmap de Evolução Técnica

Com a arquitetura modular e desacoplada já estabelecida, os seguintes aprimoramentos técnicos são os próximos passos recomendados para um ambiente produtivo em larga escala:

1. **Cache Semântico de Consultas:**
   - Implementação de cache de similaridade semântica (via Redis ou SQLite) para dúvidas recorrentes (ex.: horário, formas de pagamento), respondendo instantaneamente sem custo de LLM.
2. **Observabilidade e Avaliação Contínua (LLM Ops):**
   - Instrumentação com OpenTelemetry / LangSmith para monitoramento de latência por ferramenta e contagem de tokens por sessão.
   - Pipeline automatizado de avaliação contínua (Ragas / G-Eval) medindo fidelidade das respostas (*faithfulness*) e aderência aos guardrails.
3. **Migração dos CSVs para Banco Relacional OLTP:**
   - Evolução dos loaders em pandas para PostgreSQL com SQLAlchemy/asyncpg, permitindo concorrência ACID, reservas de estoque com controle de concorrência e integridade referencial via banco.
4. **Busca Híbrida (Dense + Sparse/BM25):**
   - Combinação de embeddings densos com busca por palavras-chave exatas (BM25 com RRF - *Reciprocal Rank Fusion*) para localização infalível de códigos de rastreio, modelos alfanuméricos específicos e artigos exatos do manual.
5. **Streaming de Resposta:**
   - Habilitação de geração progressiva de tokens (*streaming*) no método `invoke` do agente e integração com WebSockets ou Server-Sent Events (SSE) no FastAPI, reduzindo a percepção de espera do usuário.
6. **Conteinerização:**
   - Disponibilização de `Dockerfile` multi-stage e `docker-compose.yml` com políticas de execução não-root e rotinas de healthcheck para orquestração em Kubernetes/Cloud Run.
