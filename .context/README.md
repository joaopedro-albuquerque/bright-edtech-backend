# Contexto do Projeto Bright EdTech

Este diretório contém toda a documentação de contexto do projeto, incluindo visão geral, arquitetura, decisões de design e referências técnicas.

## Índice de Documentos

- **[visao-geral.md](visao-geral.md)** — Visão geral do produto, objetivos e proposta de valor
- **[arquitetura.md](arquitetura.md)** — Stack tecnológico, infraestrutura e decisões arquiteturais
- **[dados.md](dados.md)** — Modelo de dados híbrido (PostgreSQL + S3) e estrutura de schema
- **[ux-ui.md](ux-ui.md)** — Decisões de UX/UI, fluxos e componentes principais
- **[modelos-resumo.md](modelos-resumo.md)** — Tipos de resumo suportados e System Prompts
- **[api-reference.md](api-reference.md)** — Documentação completa de todas as rotas da API, com exemplos reais de request/response, headers de auth e erros (para integração de frontend)
- **[migrations.sql](migrations.sql)** — Script SQL para atualizar banco (tokens + índices)
- **[plano-de-testes-v2.md](plano-de-testes-v2.md)** — Plano de Testes do TCC (versão ativa: cronograma, casos de teste, matriz de rastreabilidade, UAT com cliente)
- **[plano-de-testes.md](plano-de-testes.md)** — Versão anterior do Plano de Testes (mantida como registro/histórico)

## Resumo Rápido

**Bright EdTech** é uma plataforma SaaS educacional que automatiza a criação de artefatos de revisão (Resumos, Flashcards e Quizzes) usando IA, com gerenciamento de aprendizado via Spaced Repetition.

- **Frontend:** React (S3 + CloudFront)
- **Backend:** Python FastAPI (ECS Fargate + ALB)
- **Dados:** PostgreSQL + S3
- **IA:** Amazon Bedrock (Claude 3.5 Sonnet/Haiku)

---

**Último atualizado:** 2026-09-09
