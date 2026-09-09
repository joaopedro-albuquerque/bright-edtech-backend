# Stack Tecnológico e Infraestrutura

## Componentes Principais

### Frontend
- **Framework:** React (SPA)
- **Hospedagem:** AWS S3 + CloudFront
- **Funcionalidades:** 
  - Visualizador de PDF
  - Abas para Resumos, Flashcards e Quizzes
  - Editor WYSIWYG (TipTap) para edição de resumos
  - Dashboard de Daily Mix (revisão diária)

### Backend API
- **Framework:** Python FastAPI
- **Containerização:** Docker
- **Orquestração:** AWS ECS (Fargate)
- **Load Balancer:** Application Load Balancer (ALB)
- **Endpoints:** RESTful (POST, GET, PUT, DELETE)

### Banco de Dados
- **Tipo:** PostgreSQL (relacional)
- **Responsabilidade:** Metadados, árvore de diretórios, estado do algoritmo SM-2
- **Nota:** Conteúdo pesado (texto de resumos, enunciados) **nunca** é salvo aqui

### Storage de Arquivos
- **Serviço:** AWS S3
- **Armazena:** 
  - PDFs brutos (upload dos usuários)
  - Resumos em `.md` (Markdown)
  - Flashcards em `.json` (estrutura de cartões)
  - Quizzes em `.json` (questões e respostas)
  - Metadados de estado (fator de facilidade, próxima revisão)

### Inteligência Artificial
- **Plataforma:** Amazon Bedrock (via `boto3`)
- **Modelos Utilizados:**
  - **Claude 3.5 Sonnet** — Tarefas complexas (síntese de resumos, geração de questões)
  - **Claude 3.5 Haiku / Amazon Nova Micro** — Extração rápida e estruturada de JSON
- **Integração:** System Prompts injetados para garantir consistência

## Arquitetura em Diagrama

```
┌─────────────────────────────────────────────────────────┐
│                     React SPA                           │
│              (S3 + CloudFront)                          │
└─────────────────┬───────────────────────────────────────┘
                  │ HTTPS
                  ▼
┌─────────────────────────────────────────────────────────┐
│               Application Load Balancer                 │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│            FastAPI on ECS (Fargate)                     │
│         - Upload de PDFs                               │
│         - Geração de artefatos (IA)                    │
│         - Algoritmo SM-2                               │
│         - Gerenciamento de estado                      │
└──────┬──────────────────────────────────────┬──────────┘
       │                                      │
       ▼                                      ▼
┌─────────────────┐                 ┌──────────────────┐
│   PostgreSQL    │                 │   AWS S3         │
│  (Metadados)    │                 │  (Artefatos)     │
└─────────────────┘                 └──────────────────┘
       │
       └───────────────────────────┬───────────────────────┐
                                   ▼
                        ┌──────────────────────┐
                        │ Amazon Bedrock       │
                        │ (Claude 3.5 Models)  │
                        └──────────────────────┘
```

## Decisões Arquiteturais

### 1. Hybrid DB + S3 Model
- **Por quê:** Reduz custo de banco de dados, mantém alta performance
- **Trade-off:** Maior complexidade em sincronização de estado
- **Benefício:** Escalabilidade horizontal via S3

### 2. ECS Fargate vs Lambda
- **Por quê:** Garante tempo de execução suficiente para processamento de IA
- **Trade-off:** Custo fixo mínimo mesmo com pouco uso
- **Benefício:** Controle sobre ambiente e dependências

### 3. System Prompts via Bedrock
- **Por quê:** Consistência de comportamento, segurança (sem prompt injection na UI)
- **Trade-off:** Requer ajuste fino por testes/feedback
- **Benefício:** Qualidade previsível de geração

## Fluxo de Processamento

### Upload de PDF
```
1. Frontend envia POST /upload com arquivo
2. API salva em S3 (bucket raw/pdfs/)
3. API cria registro em BD (documentos, status='processando')
4. Trigger async: Extrai texto e gera metadados
5. Status muda para 'pronto'
```

### Geração de Artefatos
```
1. Usuário solicita resumo/flashcard/quiz
2. API extrai configuração (doc > pasta > perfil)
3. Bedrock processa com System Prompt injetado
4. Resultado salvo em S3 (bucket artifacts/)
5. Referência (s3_chave) salva em BD
6. Frontend exibe editor (resumo) ou visualizador
```

### Daily Mix (Revisão)
```
1. Frontend aciona GET /daily-mix
2. API busca em BD: flashcards/questões com proxima_revisao <= hoje
3. Frontend exibe itens para revisar
4. Usuário responde e classifica (1-5)
5. API aplica SM-2, recalcula proxima_revisao
6. BD atualizado, usuário vê "próxima revisão" atualizada
```

## Segurança e Performance

- **CORS:** Configurado para origem S3/CloudFront
- **Auth:** JWT (tokens de sessão) — detalhes em docs separadas
- **Rate Limiting:** Implementado por usuário
- **Caching:** CloudFront para assets estáticos, Redis para cache de sessões (opcional)
