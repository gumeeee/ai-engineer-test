# Config Layer

## Responsabilidade
Gerenciar todas as configurações via variáveis de ambiente usando Pydantic Settings.
Expõe um singleton `settings` importável por qualquer camada.

## Exporta
- `settings` — instância singleton de `Settings`
- `Settings` — classe de configuração

## Regras
- NUNCA importar nada de `agents/`, `rag/`, `api/`, `core/`, `tools/`
- Apenas tipos primitivos e Pydantic Settings
- Toda variável de ambiente do projeto passa por aqui