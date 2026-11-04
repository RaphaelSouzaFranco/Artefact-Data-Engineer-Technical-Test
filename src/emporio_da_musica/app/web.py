"""Interface Web conversacional amigável em Gradio para o Empório da Música."""

from __future__ import annotations

import uuid
from typing import List, Tuple

import gradio as gr
from langchain_core.messages import HumanMessage

from emporio_da_musica.agent import EmporioAgent

# Instância compartilhada do agente
agent = EmporioAgent()


def respond(message: str, history: List[dict], thread_id: str) -> Tuple[str, List[dict]]:
    """Gera a resposta do agente e anexa ao formato de mensagens do Chatbot do Gradio."""
    if not message.strip():
        return "", history

    # Invocar agente mantendo histórico pela thread_id
    resposta_ai = agent.invoke([HumanMessage(content=message)], thread_id=thread_id)

    # Novo padrão de formato dict {"role": ..., "content": ...} do Gradio Chatbot
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": resposta_ai.content})

    return "", history


def reset_session() -> Tuple[str, List[dict]]:
    """Cria uma nova sessão isolada."""
    new_thread_id = str(uuid.uuid4())[:8]
    return new_thread_id, []


def create_app() -> gr.Blocks:
    with gr.Blocks(title="Empório da Música — Atendimento Virtual") as demo:
        gr.Markdown(
            """
            # 🎸 Empório da Música — Atendimento ao Cliente
            *Loja especializada em instrumentos musicais — Campo Grande / MS*
            
            Consulte nosso catálogo, tire dúvidas sobre políticas de entrega/troca ou verifique o status do seu pedido!
            """
        )

        with gr.Row():
            thread_id_state = gr.State(lambda: str(uuid.uuid4())[:8])
            thread_display = gr.Textbox(
                label="ID da Sessão (Thread ID)",
                interactive=False,
                scale=3,
            )
            btn_novo = gr.Button("🔄 Nova Conversa", scale=1)

        chatbot = gr.Chatbot(
            label="Conversa",
            height=500,
        )

        with gr.Row():
            msg_input = gr.Textbox(
                label="Digite sua mensagem",
                placeholder="Ex: Vocês têm violão Takamine? | Como funciona o frete para Campo Grande?",
                scale=8,
                lines=2,
            )
            btn_enviar = gr.Button("Enviar 🎵", scale=2, variant="primary")

        # Exemplos de uso rápido
        gr.Examples(
            examples=[
                "Vocês têm violão da Takamine em estoque?",
                "Como funciona o frete para Campo Grande?",
                "Qual o horário de funcionamento da loja?",
                "Como funciona a política de devolução por arrependimento?",
                "Gostaria de verificar o status do meu pedido 8",
            ],
            inputs=msg_input,
        )

        # Atualizar exibição inicial da thread
        demo.load(fn=lambda tid: tid, inputs=[thread_id_state], outputs=[thread_display])

        # Eventos de envio
        msg_input.submit(
            fn=respond,
            inputs=[msg_input, chatbot, thread_id_state],
            outputs=[msg_input, chatbot],
        )
        btn_enviar.click(
            fn=respond,
            inputs=[msg_input, chatbot, thread_id_state],
            outputs=[msg_input, chatbot],
        )

        # Evento de nova sessão
        btn_novo.click(
            fn=reset_session,
            inputs=[],
            outputs=[thread_id_state, chatbot],
        ).then(
            fn=lambda tid: tid,
            inputs=[thread_id_state],
            outputs=[thread_display],
        )

    return demo


def main() -> None:
    app = create_app()
    app.launch()


if __name__ == "__main__":
    main()

