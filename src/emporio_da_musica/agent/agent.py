"""Orquestrador do Agente de Atendimento Empório da Música."""

from __future__ import annotations

from typing import Any, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from emporio_da_musica import config
from emporio_da_musica.agent.prompts import SYSTEM_PROMPT
from emporio_da_musica.memory import SQLiteConversationMemory
from emporio_da_musica.tools import ALL_TOOLS


class EmporioAgent:
    """Agente de atendimento conversacional com ReAct / Function Calling nativo e memória persistente."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.2,
        llm: Optional[Any] = None,
        tools: Optional[List[Any]] = None,
        memory: Optional[SQLiteConversationMemory] = None,
    ):
        self.tools = tools or ALL_TOOLS
        self.tools_by_name = {t.name: t for t in self.tools}
        self.memory = memory or SQLiteConversationMemory()

        if llm is not None:
            self.llm = llm
        else:
            self.llm = ChatGoogleGenerativeAI(
                model=model_name or config.CHAT_MODEL,
                temperature=temperature,
                google_api_key=config.GOOGLE_API_KEY,
            )

        # Vincular ferramentas com function calling nativo do Gemini
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    def invoke(
        self,
        messages: List[BaseMessage],
        thread_id: Optional[str] = None,
    ) -> AIMessage:
        """Executa um ciclo completo de raciocínio e function calling até resposta final.
        
        Se thread_id for fornecido, recupera o histórico persistido antes de rodar
        e salva as novas mensagens ao final.
        """
        full_history: List[BaseMessage] = []

        # 1. Recuperar histórico prévio se houver thread_id
        if thread_id:
            prior_messages = self.memory.get_messages(thread_id)
            full_history.extend(prior_messages)

        # 2. Garantir system prompt inicial
        if not full_history or not isinstance(full_history[0], SystemMessage):
            full_history.insert(0, SystemMessage(content=SYSTEM_PROMPT))

        # 3. Adicionar as novas mensagens de entrada
        full_history.extend(messages)
        start_idx_new_messages = len(full_history) - len(messages)

        # Loop de Function Calling (máximo de 5 passos)
        for _ in range(5):
            ai_msg = self.llm_with_tools.invoke(full_history)
            full_history.append(ai_msg)

            # Se não houver chamadas de ferramenta, encerra com a resposta final
            if not getattr(ai_msg, "tool_calls", None):
                # Normalizar caso o conteúdo venha em lista de blocos (padrão v3/Interactions API)
                if isinstance(ai_msg.content, list):
                    texts = [
                        item.get("text", "")
                        for item in ai_msg.content
                        if isinstance(item, dict) and item.get("type") == "text"
                    ]
                    ai_msg.content = "".join(texts)

                # 4. Salvar histórico da sessão se thread_id foi fornecido
                if thread_id:
                    # Salva as novas mensagens geradas neste turno
                    novas_para_salvar = full_history[start_idx_new_messages:]
                    self.memory.append_messages(thread_id, novas_para_salvar)

                return ai_msg

            # Executar as ferramentas chamadas pelo modelo
            for tool_call in ai_msg.tool_calls:
                t_name = tool_call["name"]
                t_args = tool_call["args"]
                tool_fn = self.tools_by_name.get(t_name)

                if tool_fn is not None:
                    try:
                        tool_res = tool_fn.invoke(t_args)
                    except Exception as e:
                        tool_res = {
                            "status": "erro",
                            "mensagem": f"Erro interno ao executar {t_name}: {str(e)}",
                        }
                else:
                    tool_res = {
                        "status": "erro",
                        "mensagem": f"Ferramenta desconhecida: {t_name}",
                    }

                # Adicionar ToolMessage ao histórico
                from langchain_core.messages import ToolMessage

                tool_message = ToolMessage(
                    content=str(tool_res),
                    name=t_name,
                    tool_call_id=tool_call["id"],
                )
                full_history.append(tool_message)

        # Se atingir o limite de iterações, força síntese final
        return full_history[-1]  # type: ignore[return-value]

