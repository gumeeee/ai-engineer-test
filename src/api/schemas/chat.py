import uuid

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = (
        Field(
            default_factory=lambda: str(uuid.uuid4()),
            description=(
                "Identificador único da sessão. Reutilize o mesmo ID para manter "
                "o histórico da conversa entre requisições."
            ),
            examples=list("550e8400-e29b-41d4-a716-446655440000"),
        ),
    )  # type: ignore
    message: str = Field(
        description="Pergunta ou mensagem sobre viagens a ser processada pelos agentes.",
        examples=list("Qual o limite de bagem de mão na LATAM?"),
        min_length=1,
        max_length=2000,
    )
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "summary": "Pergunta sobre política de bagagem (FAQ Agent)",
                    "value": {
                        "session_id": "550e8400-e29b-41d4-a716-446655440000",
                        "message": "Qual o limite de bagagem de mão na LATAM?",
                    },
                },
                {
                    "summary": "Busca de preços em tempo real (Search Agent)",
                    "value": {
                        "session_id": "550e8400-e29b-41d4-a716-446655440001",
                        "message": "Quais são as promoções de passagens para Miami?",
                    },
                },
                {
                    "summary": "Pergunta híbrida (FAQ + Search)",
                    "value": {
                        "session_id": "550e8400-e29b-41d4-a716-446655440002",
                        "message": "Qual a política de remarcação da Azul e quais voos ela opera para Recife hoje?",
                    },
                },
            ],
        }
    }


class ChatResponse(BaseModel):
    session_id: str = Field(
        description="Identificador da sessão, ecoado da requisição."
    )
    response: str = Field(
        description="Resposta final consolidada gerada pelos agentes."
    )
    agent_used: str = Field(
        description="Agente que gerou a resposta: `faq`, `search` ou `both`.",
        examples=list("faq"),
    )
    sources: list[str] = Field(
        description=(
            "Referências utilizadas para gerar a resposta. "
            "Para o FAQ Agent: seções do manual PDF. "
            "Para o Search Agent: URLs das fontes."
        ),
        examples=[["manual-politicas-viagem-blis.pdf - Seção 1.1"]],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "response": (
                        "A bagagem de mão na LATAM tem dimensão máxima de 115cm "
                        "(C+L+A) e peso máximo de 10kg. Você pode levar 1 mala + "
                        "1 item pessoal."
                    ),
                    "agent_used": "faq",
                    "sources": ["manual-politicas-viagem-blis.pdf - Seção 1.1"],
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    status: str = Field(
        description="Status geral da aplicação.",
        examples=list("healthy"),
    )
    redis: str = Field(
        description="Status da conexão com o Redis (`connected` ou `disconnected`).",
        examples=list("connected"),
    )
    vectorstore: str = Field(
        description="Status do ChromaDB (`ready`, `empty` ou `error`).",
        examples=list("ready"),
    )
    version: str = Field(
        description="Versão da aplicação.",
        examples=list("0.1.0"),
    )
