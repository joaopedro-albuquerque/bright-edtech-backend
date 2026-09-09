# Glossário de Termos — Bright EdTech

## Termos Técnicos

### Bedrock
Serviço AWS que fornece acesso a modelos de IA da Anthropic, Meta, Stability AI e outros. Usado para geração de resumos, flashcards e quizzes.

### CloudFront
Content Delivery Network (CDN) da AWS. Distribui assets estáticos do React SPA globalmente com baixa latência.

### ECS (Elastic Container Service)
Serviço de orquestração de containers da AWS. Gerencia instâncias de FastAPI rodando em Fargate (serverless containers).

### Fargate
Plataforma AWS para rodar containers sem gerenciar servidores. Elimina necessidade de EC2 instances dedicadas.

### S3 (Simple Storage Service)
Armazenamento de objetos da AWS. Usado para:
- PDFs brutos (uploads)
- Resumos em Markdown
- Flashcards e Quizzes em JSON
- Metadados de configuração

### PostgreSQL
Banco de dados relacional open-source. Armazena metadados, estrutura de diretórios e estado do SM-2.

### TipTap
Editor WYSIWYG (What You See Is What You Get) baseado em Vue.js. Renderiza Markdown de resumos com suporte a edição visual.

### FastAPI
Framework web Python moderno para construir APIs RESTful. Fornece validação automática, documentação Swagger e suporte assíncrono.

---

## Conceitos de UX/UI

### Soft Gating
Estratégia de onboarding que permite uso da plataforma sem verificação obrigatória de email. Reduz atrito de entrada.

### Document Hub
Interface central onde usuário trabalha com um PDF específico. Exibe visualizador de PDF + abas de Resumos/Flashcards/Quizzes lado-a-lado.

### Daily Mix / Túnel de Foco
Dashboard unificado na Home que mostra todos os flashcards e questões prontos para revisão (proxima_revisao <= hoje).

### Herança de Configuração
Sistema em cascata onde preferências de IA seguem prioridade:
1. Documento
2. Pasta
3. Perfil Global

---

## Conceitos de Algoritmo

### SM-2 (SuperMemo 2)
Algoritmo de repetição espaçada que otimiza retenção de longo prazo. Ajusta intervalo de revisão baseado em dificuldade relatada.

**Fórmula:**
```
novo_EF = max(1.3, EF + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02)))
novo_intervalo = intervalo_anterior * novo_EF
proxima_revisao = hoje + novo_intervalo (se grade >= 3)
```

**Parâmetros:**
- `fator_facilidade` (EF): Começa em 2.5, varia de 1.3 a 5.0
- `intervalo_atual`: Dias desde última revisão
- `repeticoes`: Contagem de vezes revisado
- `proxima_revisao`: Timestamp da próxima exibição

### Spaced Repetition
Técnica cognitiva que distribui revisão ao longo do tempo. Contrasta com cramming (estudo concentrado). Maximiza retenção com menos esforço.

### Grade (Classificação de Dificuldade)
Escala 1-5 que usuário seleciona após revisar um item:
- **5** = Muito fácil → Intervalo grande
- **4** = Fácil → Intervalo médio
- **3** = Médio → Intervalo pequeno (mínimo para progresso)
- **2** = Difícil → Volta para amanhã
- **1** = Muito difícil → Volta hoje à noite

---

## Conceitos de Dados

### Hybrid DB + S3 Model
Arquitetura onde dados pesados (conteúdo de artefatos) ficam em S3, e metadados/estado em PostgreSQL. Reduz custo DB, mantém performance.

### s3_chave
Path completo de um arquivo em S3. Exemplo: `artifacts/user-123/doc-456/resumo-001.md`

### item_ref
Identificador único dentro de um arquivo JSON. Exemplo: `card_001` dentro de um flashcard.

### Status de Documento
Estados possíveis:
- `pendente`: Aguardando processamento
- `processando`: Extração de texto em andamento
- `pronto`: Pronto para geração de artefatos
- `erro`: Falha no processamento

---

## Modelos de Resumo

### Resumo Executivo
Bullet points diretos (5-7 tópicos) para leitura rápida. Ideal para revisão.

### Método Cornell
Formato com Perguntas-Gatilho | Notas de Estudo | Sumário. Ideal para estudo ativo.

### Fichamento Acadêmico
Formato formal com Citações Diretas, Metodologia e Apreciação Crítica. Ideal para pesquisa.

---

## Componentes de Negócio

### SaaS
Software as a Service — modelo de negócio onde software é oferecido como serviço em nuvem, geralmente com cobrança por assinatura.

### Freemium
Modelo comercial onde versão básica é gratuita, e recursos premium são pagos.

### Onboarding
Processo de integração de novo usuário. Inclui cadastro, verificação, perfil inicial.

### Retenção
Métrica de negócio: percentual de usuários que continuam usando o produto. Daily Mix visa melhorar retenção via engajamento.

---

## Acrônimos Comuns

| Acrônimo | Significado | Contexto |
|--|--|--|
| SM-2 | SuperMemo 2 | Algoritmo de repetição espaçada |
| ALB | Application Load Balancer | AWS, roteamento de tráfego |
| ECS | Elastic Container Service | AWS, orquestração de containers |
| API | Application Programming Interface | Interface de comunicação entre sistemas |
| WYSIWYG | What You See Is What You Get | Editor visual (TipTap) |
| ABNT | Associação Brasileira de Normas Técnicas | Formato de citação (Brasil) |
| APA | American Psychological Association | Formato de citação (internacional) |
| JSON | JavaScript Object Notation | Formato de dados estruturado |
| PDF | Portable Document Format | Formato de arquivo |
| SPA | Single Page Application | Frontend (React) |
| IA | Inteligência Artificial | Geração de conteúdo (Bedrock) |
| IA | Artificial Intelligence | Geração de conteúdo (Bedrock) |

---

## Termos de Negócio

### Usuário Verificado
Usuário que completou verificação de email. Pode ter restrições diferentes vs. não-verificado.

### Quota / Limite Mensal
Quantidade máxima de resumos/flashcards que usuário pode gerar por mês (varies by plan).

### Premium / Plano Pago
Assinatura paga com limite aumentado, features exclusivas.

### Tokens de IA
Unidade de cobrança de LLM. Cada token ≈ 4 caracteres. Rastreado em `resumos.tokens_utilizados`.

---

## Tipos de Dados em S3

| Tipo | Extensão | Exemplo Path | Conteúdo |
|--|--|--|--|
| PDF bruto | `.pdf` | `uploads/user-123/doc-456.pdf` | PDF original do usuário |
| Resumo | `.md` | `artifacts/user-123/doc-456/resumo-001.md` | Markdown renderizado |
| Flashcard | `.json` | `artifacts/user-123/doc-456/flashcard-001.json` | Array de pares Q&A |
| Quiz | `.json` | `artifacts/user-123/doc-456/quiz-001.json` | Array de questões |

---

## Fluxos Principais

### Upload de PDF
```
Frontend → API (PUT /api/documents) → S3 (PDF bruto) → BD (metadata)
```

### Geração de Resumo
```
Frontend → API → Bedrock → S3 (arquivo .md) → BD (referência)
```

### Revisão Diária (Daily Mix)
```
Frontend → API (GET /daily-mix) → BD (cartoes WHERE proxima_revisao <= hoje)
→ Frontend exibe → Usuário responde → API (POST /cartoes/{id}/responder)
→ SM-2 calcula → BD atualiza
```

---

## Recursos Externos

- **AWS Documentation:** https://docs.aws.amazon.com/
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **SM-2 Algorithm:** https://en.wikipedia.org/wiki/Spaced_repetition#SM-2
- **TipTap Editor:** https://www.tiptap.dev/
- **Bedrock Models:** https://docs.aws.amazon.com/bedrock/latest/userguide/models-support.html
