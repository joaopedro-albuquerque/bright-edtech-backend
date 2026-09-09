# Referência Rápida — Bright EdTech

## Stack em uma linha
**React (S3+CloudFront) → FastAPI (ECS) → PostgreSQL + S3 + Bedrock**

---

## Arquitetura de Dados (Hibrid Model)

```
CONTEÚDO → S3 (Resumos .md, Flashcards .json, Quizzes .json)
METADADOS → PostgreSQL (Usuários, Pastas, Docs, Refs a S3, Estado SM-2)
IA → Bedrock (Claude 3.5 Sonnet/Haiku via System Prompts)
```

---

## Tabelas PostgreSQL Essenciais

| Tabela | Chave | Função |
|--|--|--|
| `usuarios` | `id` | Cadastro, preferências globais |
| `pastas` | `id` | Hierarquia de diretórios |
| `documentos` | `id`, `s3_chave` | PDFs uploadados + status |
| `resumos` | `id`, `documento_id` | Refs a arquivos .md em S3 |
| `flashcards` | `id`, `documento_id` | Refs a arquivos .json em S3 |
| `cartoes` | `id`, `flashcard_id` | **Estado SM-2** (fator, intervalo, proxima_revisao) |
| `quizzes` | `id`, `documento_id` | Refs a .json com questões |
| `questoes` | `id`, `quiz_id` | **Estado SM-2** (idem cartoes) |

---

## Modelos de Resumo (3 tipos)

| Modelo | Uso | Formato | Tempo |
|--|--|--|--|
| **Executivo** | Revisão rápida | Bullet points | 3-5 min |
| **Cornell** | Estudo ativo | Pergunta \| Resposta | 10-15 min |
| **Fichamento** | Pesquisa formal | Citações + Crítica | 15-20 min |

---

## Fluxo de Usuário (Happy Path)

```
1️⃣  Cadastro + Onboarding
    → Perfil global (modelo de resumo, estilo, ritmo)

2️⃣  Upload de PDF
    → API salva em S3, marca como 'pronto'

3️⃣  Gera Artefatos (Resumos/Flashcards/Quizzes)
    → Bedrock processa, salva em S3
    → BD guarda referência

4️⃣  Abre Document Hub (PDF + abas)
    → Lê resumo, estuda flashcards, resolve quizzes

5️⃣  Daily Mix (Revisão Diária)
    → Frontend busca itens com proxima_revisao <= hoje
    → Usuário responde (grade 1-5)
    → SM-2 recalcula data de próxima revisão

6️⃣  Repeat → Engajamento contínuo
```

---

## Endpoints API Principais

> Endpoints reais (v1, implementados). `X-User-Id` é obrigatório nas rotas que usam
> `get_current_user_id`.

### Perfil / Usuário
```
POST   /profile                       # Cadastro
GET    /profile                       # Busca por token (Cognito)
GET    /profile/{user_id}             # Detalhe
PUT    /profile/{user_id}             # Editar perfil completo
DELETE /profile/{user_id}             # Deletar conta
GET    /profile/{user_id}/dashboard   # Dashboard consolidado
POST   /profile/{user_id}/perfil      # Onboarding (estilo/formato/objetivos)
```

### Pastas
```
POST   /pastas                        # Criar
GET    /pastas/user/{user_id}         # Pastas raiz
GET    /pastas/user/{user_id}/todas   # Todas as pastas
GET    /pastas/{pasta_id}/conteudo    # Subpastas + documentos
PUT    /pastas/{pasta_id}             # Renomear
DELETE /pastas/{pasta_id}             # Deletar
```

### Documentos
```
POST   /documentos/upload                     # Upload PDF
GET    /documentos/{id}/url-visualizacao       # URL pré-assinada (S3)
PUT    /documentos/{id}                        # Renomear
DELETE /documentos/{id}                        # Deletar
```

### Resumos (Bedrock)
```
POST   /documentos/{documento_id}/resumos   # Gerar (body: nivel_conhecimento, formato, tom)
DELETE /resumos/{resumo_id}                 # Deletar
```

### Flashcards (Bedrock)
```
POST   /documentos/{documento_id}/flashcards   # Gerar (body: quantidade)
DELETE /flashcards/{flashcard_id}              # Deletar
```

### Quizzes (Bedrock)
```
POST   /documentos/{documento_id}/quizzes   # Gerar (body: quantidade)
DELETE /quizzes/{quiz_id}                   # Deletar
```

### Revisões / Daily Mix (SM-2)
```
GET  /revisoes/hoje                            # Daily Mix consolidado (cartões + questões)
GET  /revisoes/flashcards                      # Só cartões pendentes
GET  /revisoes/quizzes                         # Só questões pendentes
PUT  /revisoes/cartoes/{cartao_id}/avaliar     # body: {qualidade: 1-5}
PUT  /revisoes/questoes/{questao_id}/avaliar   # body: {qualidade: 1-5}
```

---

## SM-2 Rápido

Implementado em [`app/services/SpacedRepetitionService.py`](../app/services/SpacedRepetitionService.py).

**Qualidade (1-5)** informada pelo usuário após ver a resposta:
- **q < 3** (errou) → `repeticoes = 0`, `intervalo_atual = 1`
- **q >= 3** (acertou):
  - `repeticoes == 0` → `intervalo_atual = 1`
  - `repeticoes == 1` → `intervalo_atual = 6`
  - `repeticoes > 1`  → `intervalo_atual = ceil(intervalo_anterior * EF_atual)`
  - `repeticoes += 1`

**Fator de Facilidade (EF):**
```
EF_novo = EF_atual + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
EF_novo = max(1.3, EF_novo)   # nunca abaixo de 1.3
```
EF inicial de qualquer cartão/questão novo: **2.5**.

**Estado Armazenado** (tabelas `cartoes` e `questoes`, mesma estrutura):
- `fator_facilidade` (EF) — começa 2.5, mínimo 1.3
- `intervalo_atual` — dias até a próxima revisão
- `repeticoes` — acertos consecutivos (nota >= 3)
- `proxima_revisao` — TIMESTAMP = agora + intervalo_atual dias

---

## Herança de Configuração

```
┌─ Configuração do Documento (máxima prioridade)
├─ Configuração da Pasta (média)
└─ Configuração Global (mínima)
```

**Exemplo:** "Para este PDF, use Fichamento Acadêmico"
→ Sobrescreve config da pasta e global.

---

## Estrutura de Pastas (S3)

```
s3://bright-bucket/
├── uploads/
│   └── user-{id}/
│       └── {document-id}.pdf
│
└── artifacts/
    └── user-{id}/
        └── doc-{id}/
            ├── resumo-{id}.md
            ├── flashcard-{id}.json
            └── quiz-{id}.json
```

---

## Variables de Ambiente (.env)

```env
# AWS
AWS_REGION=us-east-1
S3_BUCKET_NAME=bright-bucket
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# PostgreSQL (ver app/core/database.py)
DB_HOST=localhost
DB_NAME=brightedtech

# Bedrock
BEDROCK_REGION=us-east-1
BEDROCK_MODEL_SUMMARY=claude-3-5-sonnet-20241022
BEDROCK_MODEL_EXTRACT=claude-3-5-haiku-20241022

# API
FASTAPI_PORT=8000
JWT_SECRET=...

# Frontend
REACT_APP_API_URL=https://api.bright-edtech.com
REACT_APP_S3_BUCKET=bright-bucket
```

---

## Comandos Úteis

### Backend (FastAPI)
```bash
# Instalar deps
pip install -r requirements.txt

# Rodar local
uvicorn app.main:app --reload

# Rodar testes
pytest tests/

# Build Docker
docker build -t bright-api .

# Deploy para ECS
aws ecs update-service --cluster bright --service api --force-new-deployment
```

### Database (PostgreSQL)
```bash
# Conectar
psql -h {DB_HOST} -U {DB_USER} -d bright_db

# Criar schema
psql -h {DB_HOST} -U {DB_USER} -d bright_db -f schema.sql

# Backup
pg_dump -h {DB_HOST} -U {DB_USER} bright_db > backup.sql

# Restore
psql -h {DB_HOST} -U {DB_USER} bright_db < backup.sql
```

### Frontend (React)
```bash
# Instalar deps
npm install

# Dev server
npm start

# Build
npm run build

# Deploy para S3+CloudFront
aws s3 sync build/ s3://bright-bucket/app/
aws cloudfront create-invalidation --distribution-id {ID} --paths "/*"
```

---

## Desafios e Trade-offs

| Decisão | Benefício | Trade-off |
|--|--|--|
| **Hybrid DB+S3** | Escalabilidade, baixo custo DB | Maior complexidade de sync |
| **ECS Fargate** | Escalabilidade horizontal | Custo fixo mínimo |
| **System Prompts** | Consistência de qualidade | Precisa de ajuste fino |
| **Soft Gating** | Menos atrito | Menos dados iniciais |
| **Document Hub** | Contexto visual | Interface densa (mobile) |
| **SM-2** | Retenção otimizada | Algoritmo complexo |

---

## Checklist: Novo Endpoint

```
1. [ ] Definir rota em FastAPI (POST/GET/PUT/DELETE)
2. [ ] Validar input com Pydantic models
3. [ ] Implementar lógica (BD + S3)
4. [ ] Testar unitariamente
5. [ ] Documentar no docstring
6. [ ] Testar integração (API local + BD)
7. [ ] Deploy: Build Docker, push ECR, update ECS
8. [ ] Teste em staging
9. [ ] Deploy em produção
10. [ ] Monitorar logs (CloudWatch)
```

---

## Checklist: Novo Recurso

```
1. [ ] Especificar requisito (UX/API/DB)
2. [ ] Design: DB schema (se necessário)
3. [ ] Desenvolvimento backend (FastAPI + DB)
4. [ ] Testes backend (unitário + integração)
5. [ ] Desenvolvimento frontend (React)
6. [ ] Testes frontend (unitário + e2e)
7. [ ] Teste combinado (local dev)
8. [ ] Deploy staging
9. [ ] QA validation
10. [ ] Deploy produção
11. [ ] Monitoramento (métricas, erros)
12. [ ] Documentação atualizada
```

---

## Links Importantes

- **AWS Console:** https://console.aws.amazon.com
- **GitHub:** https://github.com/bright-edtech/bright-edtech-backend
- **Jira/Linear:** (Onde tickets de desenvolvimento estão)
- **Datadog/CloudWatch:** (Monitoramento)
- **Slack:** (Comunicação do time)

---

## Próximas Etapas (Típicas)

1. 🔒 Implementar autenticação JWT
2. 📝 Adicionar edição de nomes (documentos, pastas)
3. 🎨 Customização de themes de resumo
4. 📊 Dashboard de analytics (uso, retenção)
5. 🔔 Notificações de Daily Mix (email, push)
6. 🌍 Suporte a múltiplos idiomas
7. 📱 App mobile nativa (React Native)
8. 🤖 Feedback loop para melhoria de prompts

---

**Última atualização:** 2026-09-09
**Responsável:** Contexto do Projeto
**Status:** V1 — Em produção
