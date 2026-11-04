"""Fase 4 — Testes unitários do orquestrador do Agente (usando Mocks, sem chamadas reais)."""

from unittest.mock import MagicMock
from langchain_core.messages import AIMessage, HumanMessage
from emporio_da_musica.agent.agent import EmporioAgent


def test_agent_resposta_direta_sem_tools():
    # Mock do LLM respondendo diretamente sem tool_calls
    mock_llm = MagicMock()
    mock_bound = MagicMock()
    mock_llm.bind_tools.return_value = mock_bound
    
    mock_bound.invoke.return_value = AIMessage(
        content="Olá! Sou o assistente da Empório da Música. Como posso ajudar com seu instrumento hoje?"
    )

    agent = EmporioAgent(llm=mock_llm)
    resposta = agent.invoke([HumanMessage(content="Olá, boa tarde!")])

    assert "Empório da Música" in resposta.content
    assert mock_bound.invoke.call_count == 1


def test_agent_execucao_de_tool_com_sucesso():
    mock_llm = MagicMock()
    mock_bound = MagicMock()
    mock_llm.bind_tools.return_value = mock_bound

    # Passo 1: LLM decide chamar a tool buscar_produto
    passo1_msg = AIMessage(
        content="",
        tool_calls=[{
            "name": "buscar_produto",
            "args": {"termo_busca": "takamine"},
            "id": "call_123",
        }],
    )
    # Passo 2: LLM recebe o resultado da tool e sintetiza a resposta final
    passo2_msg = AIMessage(
        content="Temos excelentes violões Takamine em estoque, como o modelo GD20 por R$ 2.199,00!"
    )

    mock_bound.invoke.side_effect = [passo1_msg, passo2_msg]

    agent = EmporioAgent(llm=mock_llm)
    resposta = agent.invoke([HumanMessage(content="Vocês têm violão Takamine?")])

    assert "Takamine" in resposta.content
    assert mock_bound.invoke.call_count == 2


def test_agent_guardrail_recusa():
    mock_llm = MagicMock()
    mock_bound = MagicMock()
    mock_llm.bind_tools.return_value = mock_bound

    mock_bound.invoke.return_value = AIMessage(
        content="Sou um especialista em instrumentos musicais da Empório da Música. Não consigo te passar receitas de bolo, mas se quiser aprender a tocar violão, estou à disposição!"
    )

    agent = EmporioAgent(llm=mock_llm)
    resposta = agent.invoke([HumanMessage(content="Me ensina uma receita de bolo de cenoura?")])

    assert "especialista em instrumentos" in resposta.content
    assert not getattr(resposta, "tool_calls", None)

