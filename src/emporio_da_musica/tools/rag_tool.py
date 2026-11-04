"""Ferramenta (tool) LangChain para que o agente consulte o RAG de políticas."""

from typing import Any, List
from langchain_core.tools import tool

from emporio_da_musica.rag.retriever import PolicyRetriever

_retriever_instance = None


def get_retriever() -> PolicyRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = PolicyRetriever()
    return _retriever_instance


@tool
def consultar_politicas_da_loja(duvida: str) -> dict[str, Any]:
    """Consulta o manual oficial de políticas e procedimentos da Empório da Música.
    
    Use esta ferramenta para responder dúvidas institucionais ou estáticas, como:
    - Horário de funcionamento e atendimento
    - Endereço físico, contato, CNPJ da loja
    - Regras de parcelamento e formas de pagamento aceitas
    - Política de trocas, devoluções e direito de arrependimento
    - Prazos e taxas de entrega/frete para Campo Grande e outras cidades
    - Regras de garantia de produtos e LGPD/privacidade
    
    Args:
        duvida: A pergunta ou tema específico a ser consultado (ex: 'qual o horário de funcionamento no sábado?', 'como funciona troca por arrependimento?').
    """
    try:
        retriever = get_retriever()
        resultados = retriever.get_relevant_policy(duvida, top_k=2)
        
        secoes = []
        for r in resultados:
            secoes.append({
                "secao": r["section_title"],
                "conteudo": r["content"],
                "relevancia": round(r["score"], 3),
            })

        return {
            "status": "sucesso",
            "duvida": duvida,
            "secoes_encontradas": secoes,
        }
    except Exception as e:
        return {
            "status": "erro",
            "mensagem": f"Não foi possível consultar as políticas no momento: {str(e)}",
            "secoes_encontradas": [],
        }

