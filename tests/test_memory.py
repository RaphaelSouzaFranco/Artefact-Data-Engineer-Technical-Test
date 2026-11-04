"""Fase 5 — Testes unitários de persistência e isolamento da memória em SQLite."""

from unittest.mock import MagicMock
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from emporio_da_musica.agent.agent import EmporioAgent
from emporio_da_musica.memory.sqlite_memory import SQLiteConversationMemory


def test_sqlite_memory_append_and_get(tmp_path):
    db_file = tmp_path / "test_memory.sqlite3"
    mem = SQLiteConversationMemory(db_path=db_file)

    msg1 = HumanMessage(content="Olá, sou o Lucas")
    msg2 = AIMessage(content="Olá Lucas, como posso ajudar?")

    mem.append_messages("thread_1", [msg1, msg2])
    recuperadas = mem.get_messages("thread_1")

    assert len(recuperadas) == 2
    assert recuperadas[0].content == "Olá, sou o Lucas"
    assert isinstance(recuperadas[0], HumanMessage)
    assert recuperadas[1].content == "Olá Lucas, como posso ajudar?"
    assert isinstance(recuperadas[1], AIMessage)


def test_sqlite_memory_isolamento_entre_threads(tmp_path):
    db_file = tmp_path / "test_memory.sqlite3"
    mem = SQLiteConversationMemory(db_path=db_file)

    mem.append_messages("sessao_A", [HumanMessage(content="Mensagem da sessão A")])
    mem.append_messages("sessao_B", [HumanMessage(content="Mensagem da sessão B")])

    msgs_a = mem.get_messages("sessao_A")
    msgs_b = mem.get_messages("sessao_B")

    assert len(msgs_a) == 1
    assert msgs_a[0].content == "Mensagem da sessão A"

    assert len(msgs_b) == 1
    assert msgs_b[0].content == "Mensagem da sessão B"

    assert sorted(mem.list_threads()) == ["sessao_A", "sessao_B"]


def test_sqlite_memory_clear_thread(tmp_path):
    db_file = tmp_path / "test_memory.sqlite3"
    mem = SQLiteConversationMemory(db_path=db_file)

    mem.append_messages("thread_temp", [HumanMessage(content="Vou ser apagado")])
    assert len(mem.get_messages("thread_temp")) == 1

    mem.clear_thread("thread_temp")
    assert len(mem.get_messages("thread_temp")) == 0


def test_agent_com_persistencia_multi_turnos_mock(tmp_path):
    """Verifica se o agente carrega o histórico prévio ao receber thread_id."""
    db_file = tmp_path / "test_memory.sqlite3"
    mem = SQLiteConversationMemory(db_path=db_file)

    mock_llm = MagicMock()
    mock_bound = MagicMock()
    mock_llm.bind_tools.return_value = mock_bound

    # Respostas para Turno 1 e Turno 2
    resp_turno1 = AIMessage(content="Prazer em te conhecer, Carlos!")
    resp_turno2 = AIMessage(content="O seu nome é Carlos, conforme você me disse!")
    mock_bound.invoke.side_effect = [resp_turno1, resp_turno2]

    agent = EmporioAgent(llm=mock_llm, memory=mem)

    # Turno 1
    agent.invoke([HumanMessage(content="Meu nome é Carlos")], thread_id="t_100")
    
    # Conferir se gravou no banco
    salvas = mem.get_messages("t_100")
    assert len(salvas) == 2  # HumanMessage + AIMessage

    # Turno 2 (nova pergunta na mesma thread)
    agent.invoke([HumanMessage(content="Qual é o meu nome?")], thread_id="t_100")

    # No segundo invoke, o histórico passado para o LLM deve conter o turno 1
    segunda_chamada_args = mock_bound.invoke.call_args_list[1][0][0]
    conteudos = [m.content for m in segunda_chamada_args]
    
    assert "Meu nome é Carlos" in conteudos
    assert "Prazer em te conhecer, Carlos!" in conteudos
    assert "Qual é o meu nome?" in conteudos

    # Total salvo no banco ao final
    assert len(mem.get_messages("t_100")) == 4

