"""Interface interativa de linha de comando (CLI) para atendimento do Empório da Música."""

from __future__ import annotations

import sys
import uuid
from langchain_core.messages import HumanMessage

from emporio_da_musica.agent import EmporioAgent


def main() -> None:
    print("=" * 65)
    print(" EMPÓRIO DA MÚSICA — ASSISTENTE VIRTUAL DE ATENDIMENTO")
    print("=" * 65)
    print("Digite suas dúvidas sobre instrumentos, pedidos ou políticas.")
    print("Comandos especiais: 'sair' para encerrar | 'nova' para nova sessão.\n")

    thread_id = str(uuid.uuid4())[:8]
    print(f"[*] Sessão iniciada: thread_id={thread_id}")

    try:
        agent = EmporioAgent()
    except Exception as e:
        print(f"[!] Erro ao inicializar o agente: {e}")
        sys.exit(1)

    while True:
        try:
            user_input = input("\nVocê: ").strip()
            if not user_input:
                continue

            cmd = user_input.lower()
            if cmd in ("sair", "exit", "quit"):
                print("\nAté logo! Empório da Música agradece sua visita.")
                break

            if cmd in ("nova", "limpar", "novo"):
                thread_id = str(uuid.uuid4())[:8]
                print(f"[*] Nova sessão criada: thread_id={thread_id}")
                continue

            print("\nEmpório da Música: pensando...", end="\r", flush=True)
            resposta = agent.invoke([HumanMessage(content=user_input)], thread_id=thread_id)
            print(" " * 40, end="\r")  # Limpa a linha de 'pensando...'
            print(f"Empório da Música:\n{resposta.content}")

        except KeyboardInterrupt:
            print("\n\nAtendimento encerrado.")
            break
        except Exception as e:
            print(f"\n[!] Ocorreu um erro durante a resposta: {e}")


if __name__ == "__main__":
    main()

