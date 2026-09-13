# Plano de Testes — Bright EdTech

| | |
|---|---|
| **Projeto** | Bright EdTech — Plataforma SaaS de aprendizagem ativa com IA |
| **Trabalho** | TCC — Instituto Federal de Educação, Ciência e Tecnologia de São Paulo (IFSP) |
| **Curso** | Análise e Desenvolvimento de Sistemas (ADS) |
| **Documento** | Plano de Testes v1.1 | |
| **Cliente real (stakeholder)** | Gabriel Lima Nascimento |
| **Data de elaboração** | 07/09/2026 |
| **Prazo final de testes** | 06/11/2026 |
| **Apresentação do TCC** | 18/11/2026 |
| **Referências metodológicas** | IEEE 829 (Test Plan), ISTQB Foundation Level, Test Pyramid, Risk-Based Testing, UAT (User Acceptance Testing) |

---

## 1. Introdução

### 1.1 Objetivo do Documento

Definir a estratégia, o escopo, os critérios, o cronograma e os casos de teste que
comprovarão que o SASS do Bright EdTech atende aos requisitos funcionais e
não-funcionais especificados, com qualidade suficiente para ser apresentado e
defendido perante a banca avaliadora do TCC.
### 1.2 Contexto

O Bright EdTech é uma plataforma SaaS educacional que usa IA generativa para gerar Resumos, Flashcards e Quizzes a partir de documentos PDF, e
gerencia retenção de conhecimento via algoritmo de Repetição Espaçada.


Este plano cobre o **backend (API FastAPI)**, que é o componente avaliável e
funcional no momento da elaboração deste documento. Testes de frontend/UI, quando
aplicável, são tratados como escopo complementar (seção 1.5).

### 1.3 Cliente Real (exigência do IFSP)

O IFSP exige que o TCC seja desenvolvido para atender uma necessidade real de uma
pessoa/organização fora do ambiente acadêmico — o Bright EdTech não é apenas um
exercício técnico, tem um **cliente real** que usará (ou validará o uso
pretendido) do produto. Isso muda a natureza dos testes: não basta o sistema estar
funcionalmente correto (validado por mim, o desenvolvedor) — ele precisa ser
**validado pelo cliente** como algo que resolve o problema dele, na linguagem
dele, com a usabilidade que ele espera. Por isso este plano inclui, além dos
testes técnicos (P0-P3 automatizados), um trilho de **Testes de Aceitação com o
Cliente (UAT)** com checkpoints ao longo do cronograma — não apenas no final —
para reduzir o risco de descobrir uma divergência de expectativa a 2 semanas da
apresentação. Ver seção 3.3, seção 7.1 e o cronograma da seção 8.

### 1.4 Por que este plano importa para a banca

Um plano de testes formal demonstra domínio de engenharia de software além da
codificação: rastreabilidade requisito → teste, gestão de risco, critérios de
aceite objetivos e evidência de qualidade — pontos tipicamente avaliados em bancas
de ADS. Este documento é o artefato que sustenta a alegação "o sistema funciona"
com dados verificáveis, não apenas uma demo ao vivo. Somado à validação do
cliente real (seção 1.3), ele também sustenta a alegação "o sistema resolve o
problema certo" — o segundo pilar de avaliação típico de bancas de ADS.

### 1.5 Escopo

**Dentro do escopo:**
- API REST (FastAPI) — todos os módulos listados na seção 2.
- Integração com Amazon Bedrock (geração de conteúdo via IA).
- Integração com AWS S3 (armazenamento de artefatos).
- Persistência PostgreSQL (schema, integridade referencial, índices).
- Algoritmo de Repetição Espaçada (SM-2) — motor matemático.
- Testes não-funcionais críticos: performance de queries de revisão, segurança
  básica (autenticação por header, isolamento de dados por usuário).

**Fora do escopo (nesta rodada):**
- Testes de UI/frontend React (não implementado até a data de corte do plano).
- Testes de carga em escala de produção (>1000 usuários simultâneos) — mencionado
  como trabalho futuro na seção 14.
- Penetration testing formal (apenas verificação de isolamento de dados básica).
- Cache Redis (fora do escopo do desenvolvimento atual, conforme decisão de
  arquitetura registrada em `.context/`).

---

## 2. Itens de Teste (Módulos do Sistema)

| # | Módulo | Descrição | Componentes-chave |
|---|--------|-----------|--------------------|
| M1 | **Usuários / Perfil** | Cadastro, autenticação, onboarding | `profile.py`, `ProfileService`, `ProfileRepository` |
| M2 | **Pastas e Documentos** | CRUD de diretórios, upload de PDF para S3 | `document.py`, `DocumentGeneratorService`, `S3Service` |
| M3 | **Resumos (IA)** | Geração de resumos via Bedrock (3 formatos) | `ResumoService`, `BedrockService` |
| M4 | **Flashcards (IA)** | Geração de flashcards via Bedrock + criação de cartões SM-2 | `FlashcardService`, `FlashcardRepository` |
| M5 | **Quizzes (IA)** | Geração de quizzes via Bedrock + criação de questões SM-2 | `QuizService`, `QuizRepository` |
| M6 | **Revisão / Daily Mix (SM-2)** | Motor de repetição espaçada, fila de revisão diária | `RevisaoService`, `SpacedRepetitionService`, `RevisaoRepository` |
| M7 | **Dashboard** | Consolidação de métricas do usuário | `DashboardService`, `DashboardRepository` |
| M8 | **Não-funcionais** | Performance, segurança, integridade de dados | Transversal |

---

## 3. Estratégia de Testes

### 3.1 Níveis de Teste (Pirâmide de Testes)

```
          ▲
         / \        UAT — Cliente Real (poucos, decisivos)
        /---\       → Validação de valor: "isso resolve meu problema?"
       /     \
      /-------\     E2E / Aceitação técnica (poucos, críticos)
     /         \    → Fluxo completo: cadastro → upload → IA → revisão
    /-----------\
   /             \  Integração (moderado)
  /               \ → Service + Repository + DB real / S3 mock
 /-----------------\
/                   \ Unitário (muitos, rápidos)
/                     \ → SpacedRepetitionService, Schemas, validações isoladas
```

| Nível | Ferramenta | O que cobre | Meta de cobertura |
|---|---|---|---|
| **Unitário** | `pytest` | Regras de negócio puras (ex.: `SpacedRepetitionService`, validação de Pydantic schemas) | ≥ 80% nas regras de negócio críticas |
| **Integração** | `pytest` + Postgres de teste (Docker) + mocks de S3/Bedrock (`moto`, `unittest.mock`) | Repository ↔ Banco real; Service ↔ Repository | Todos os fluxos de escrita/leitura críticos |
| **Sistema / API** | `pytest` + `httpx.AsyncClient` / Postman-Newman | Endpoints FastAPI ponta a ponta (contrato HTTP) | 100% dos endpoints públicos |
| **Aceitação técnica (E2E)** | Roteiro manual + Postman Collection | Jornada completa do usuário (happy path do TCC) | Cenários da seção 9.8 |
| **Não-funcional** | `locust` (performance), checklist manual (segurança) | Latência do Daily Mix, isolamento multiusuário | Seção 12 |
| **Aceitação do Cliente (UAT)** | Sessões guiadas presenciais/remotas + roteiro estruturado | O sistema resolve o problema real do cliente, na linguagem dele | Seção 3.3 e 9.9 |

### 3.2 Abordagem Baseada em Risco (Risk-Based Testing)

Nem tudo tem a mesma prioridade. A matriz abaixo direciona onde investir mais
esforço de teste primeiro:

| Módulo | Probabilidade de falha | Impacto se falhar | Prioridade de teste |
|---|---|---|---|
| M6 — SM-2 (Revisão) | Média (matemática + estado) | **Alto** (é o core do produto e da tese do TCC) | 🔴 **P0 — Crítica** |
| M3/M4/M5 — Geração via IA | Alta (dependência externa, parsing de JSON da IA) | Alto (funcionalidade-chave) | 🔴 **P0 — Crítica** |
| M2 — Documentos/S3 | Média (I/O externo) | Alto (bloqueia tudo que depende de PDF) | 🟠 **P1 — Alta** |
| M1 — Usuários/Perfil | Baixa (CRUD simples) | Médio | 🟡 **P2 — Média** |
| M7 — Dashboard | Baixa (leitura agregada) | Baixo | 🟢 **P3 — Baixa** |
| M8 — Não-funcionais | Média | Médio (relevante para banca, não bloqueante) | 🟠 **P1 — Alta** |

### 3.3 Testes de Aceitação com o Cliente (UAT)

Diferente dos demais níveis, o UAT não valida "o código funciona" — valida "isso
é o que o cliente precisava". É conduzido **com o cliente presente**, sobre o
ambiente de homologação, usando a linguagem dele (não termos técnicos).

**Formato de cada sessão de UAT:**
1. Demonstrar a funcionalidade pronta (eu opero, cliente observa) — 10 min.
2. Cliente opera o sistema sozinho, com roteiro guiado (tarefas, não instruções
   passo a passo) — 15–20 min.
3. Coletar feedback estruturado: o que funcionou, o que confundiu, o que falta.
4. Registrar cada item como **Achado de UAT** (seção 3.3.1), não como bug — nem
   todo achado vira código, mas todo achado precisa de uma decisão registrada
   (aceitar como está / ajustar / adiar para pós-TCC).

**Por que checkpoints e não só uma sessão final:** validar só no fim (semana 9)
é o erro mais comum e mais caro em projetos com cliente real — qualquer
divergência de expectativa descoberta a 2 semanas da apresentação não tem tempo
de ser corrigida. Por isso o cronograma (seção 8) intercala **3 checkpoints
intermediários** com o cliente, um após cada bloco de módulos relacionados, mais
uma **sessão final de UAT formal** antes do code freeze.

#### 3.3.1 Modelo de Registro de Achado de UAT

| Campo | Descrição |
|---|---|
| ID | `UAT-XXX` |
| Data / Checkpoint | Qual sessão gerou o achado |
| Módulo relacionado | M1–M8 |
| Relato do cliente (linguagem dele) | Ex.: "não entendi o que 'nível de conhecimento' significa no formulário" |
| Interpretação técnica | Ex.: falta texto de ajuda no campo `nivel_conhecimento` |
| Decisão | Ajustar agora / Ajustar até 06/11 / Registrar como melhoria futura (pós-TCC) / Aceitar como está (justificar) |
| Responsável | Eric |
| Status | Aberto / Em tratamento / Resolvido / Adiado |

> Diferente de um bug técnico (seção 11), um achado de UAT pode ser
> legitimamente "aceito como está" se a decisão for justificada — o objetivo é
> registrar que a divergência foi **ouvida e decidida**, não necessariamente
> corrigida. Isso também é avaliado por bancas: mostra maturidade de produto.

---

## 4. Critérios de Entrada e Saída

### 4.1 Critérios de Entrada (para iniciar os testes de um módulo)
- Código do módulo mergeado na branch de desenvolvimento e compilando sem erros.
- `schema.sql` aplicado no ambiente de testes.
- Variáveis de ambiente (`.env`) configuradas (Bedrock, S3, DB).
- Casos de teste do módulo revisados (seção 9).

### 4.2 Critérios de Saída (para considerar um módulo "testado")
- 100% dos casos de teste **P0/P1** executados.
- Zero defeitos abertos com severidade **Crítica** ou **Alta**.
- Cobertura de teste unitário ≥ 80% nas classes de serviço do módulo.
- Evidência registrada (print/log/relatório do pytest) anexada à matriz de
  rastreabilidade (seção 10).

### 4.3 Critério de Saída Geral do Projeto (Go/No-Go para 18/11)
- Todos os módulos M1–M8 com critério de saída (4.2) atingido até **06/11/2026**.
- Cenário de aceitação E2E completo (seção 9.8) executado com sucesso pelo menos
  3 vezes consecutivas sem falha (estabilidade).
- Nenhum defeito Crítico/Alto em aberto na data de corte.
- **Sessão final de UAT (seção 9.9) realizada com o cliente e Termo de Aceite
  assinado** (ou achados registrados com decisão explícita — seção 3.3.1) até
  **06/11/2026**. Sem isso, o Go/No-Go não pode ser declarado, mesmo que os
  testes técnicos estejam 100% verdes: qualidade técnica sem validação do
  cliente não atende ao requisito acadêmico do IFSP.

---

## 5. Critérios de Suspensão e Retomada

| Condição de suspensão | Ação |
|---|---|
| Ambiente de banco de dados indisponível | Suspender testes de integração/sistema; manter testes unitários |
| Bedrock/S3 fora do ar ou sem credenciais válidas | Suspender M3/M4/M5; usar mocks para não bloquear cronograma |
| Defeito Crítico bloqueando >1 módulo | Suspender módulos dependentes até correção e nova build |
| Cliente indisponível para um checkpoint de UAT agendado | Reagendar dentro da mesma semana; se impossível, registrar risco (seção 14) e seguir com testes técnicos — checkpoint não pode empurrar o cronograma técnico |

Retomada ocorre assim que a condição que gerou a suspensão for sanada e uma nova
execução de smoke test (seção 9.0) confirmar estabilidade mínima.

---

## 6. Ambiente de Testes

| Ambiente | Finalidade | Dados | Observação |
|---|---|---|---|
| **Local (dev)** | Desenvolvimento e testes unitários/integração | Postgres local via Docker, bucket S3 de teste | Usado no dia a dia (Semanas 1–8) |
| **Homologação** | Ensaio geral e testes de aceitação | Cópia sanitizada do schema, dados sintéticos | Usado nas Semanas 8–9 e no code freeze |
| **Demo (apresentação)** | Ambiente estável para a banca em 18/11 | Dados de demonstração pré-carregados (seed) | Congelado a partir de 10/11 |

### 6.1 Ferramentas

| Categoria | Ferramenta |
|---|---|
| Testes unitários/integração | `pytest`, `pytest-cov`, `pytest-asyncio` |
| Mock de AWS | `moto` (S3) / mocks manuais para Bedrock (`unittest.mock`) |
| Testes de API/contrato | `httpx`, Postman + Newman (collection versionada) |
| Performance | `locust` (simulação de carga no `/revisoes/hoje`) |
| Banco de testes | PostgreSQL 15 (Docker), isolado do banco de desenvolvimento |
| Gestão de defeitos | GitHub Issues (label `bug`, `severidade:*`, `modulo:*`) |
| Rastreabilidade | Este documento (seção 10) + planilha complementar (opcional) |

---

## 7. Papéis e Responsabilidades

| Papel | Responsável | Responsabilidade |
|---|---|---|
| Autor / Dev / QA | Eric Ferreira Martins | Escrever e executar todos os testes, corrigir defeitos, manter este plano |
| **Cliente Real (stakeholder)** | *(preencher: nome/organização)* | Participar dos checkpoints de UAT (seção 7.1), validar se o sistema resolve seu problema, assinar o Termo de Aceite (seção 9.9) |
| Orientador(a) | *(preencher)* | Validar aderência acadêmica do plano, revisar cronograma |
| Banca Avaliadora | *(preencher em 18/11)* | Validar critérios de aceite na apresentação |

> Mesmo em um TCC individual, formalizar papéis é padrão de mercado e demonstra
> maturidade de processo — a banca frequentemente pergunta "quem validou isso?".
> No caso do cliente real, a resposta precisa ser verificável (registro de UAT +
> termo assinado), não apenas "conversei com ele".

### 7.1 Disponibilidade do Cliente — Combinar Previamente

Agendar com o cliente, já na Semana 1, **4 encontros fixos** (podem ser remotos,
30–45 min cada):

| Encontro | Semana alvo | Objetivo |
|---|---|---|
| Kickoff de validação | S1 (09–15/09) | Apresentar o plano, confirmar que o escopo (seção 1.5) ainda reflete a necessidade real do cliente, alinhar expectativa de uso |
| Checkpoint 1 | S3 (23–29/09) | Validar organização de pastas/documentos e upload — "consigo organizar meu material do jeito que preciso?" |
| Checkpoint 2 | S5 (07–13/10) | Validar **qualidade do conteúdo gerado pela IA** (resumos, flashcards, quizzes) — o único critério que não dá para automatizar: "isso realmente me ajudaria a estudar/ensinar?" |
| Checkpoint 3 | S7 (21–27/10) | Validar o fluxo de revisão diária (Daily Mix) de ponta a ponta |
| **UAT Final + Termo de Aceite** | S9 (04–06/11) | Roteiro formal completo (seção 9.9), assinatura do termo |

> Se o cliente só puder confirmar 1 ou 2 datas com antecedência, priorizar
> **Checkpoint 2** (qualidade da IA) e o **UAT Final** — são os que mais reduzem
> risco de reprovação por "não resolve o problema real".

---

## 8. Cronograma por Módulo

Cronograma semanal, de **09/09/2026** (hoje) até **06/11/2026** (prazo final).
Após essa data, o período de **07/11 a 17/11** é reservado como buffer de
estabilização e ensaio da apresentação — **sem novas funcionalidades**.

| Semana | Período | Módulo(s) em foco | Entregável da semana | 👤 Cliente |
|---|---|---|---|---|
| S1 | 09/09 – 15/09 | Setup: ambiente de testes, banco Docker, mocks de Bedrock/S3, esqueleto de `pytest` | Ambiente de testes funcional + CI local | **Kickoff de validação** (escopo/expectativa) |
| S2 | 16/09 – 22/09 | **M1 — Usuários/Perfil** | Casos CT-USR-* executados, cobertura ≥80% | — |
| S3 | 23/09 – 29/09 | **M2 — Pastas e Documentos** | Casos CT-DOC-* executados | **Checkpoint 1** (organização/upload) |
| S4 | 30/09 – 06/10 | **M3 — Resumos (Bedrock)** | Casos CT-RES-* executados, mocks de IA validados | — |
| S5 | 07/10 – 13/10 | **M4 + M5 — Flashcards e Quizzes (Bedrock)** | Casos CT-FLC-* e CT-QUI-* executados | **Checkpoint 2** (qualidade do conteúdo gerado por IA) ⭐ |
| S6 | 14/10 – 20/10 | **M6 — Revisão / SM-2 (crítico)** | Casos CT-REV-* executados, validação matemática do algoritmo | — |
| S7 | 21/10 – 27/10 | **M7 — Dashboard** + Integração E2E entre todos os módulos | Cenário de aceitação (9.8) executado 1ª vez | **Checkpoint 3** (fluxo de revisão diária) |
| S8 | 28/10 – 03/11 | **M8 — Não-funcionais** (performance, segurança) + regressão geral | Relatório de performance + checklist de segurança | Consolidar achados de UAT pendentes |
| S9 | 04/11 – 06/11 | **Code freeze**, smoke test final, homologação, Go/No-Go | Relatório final de testes assinado (Go) | **UAT Final + Termo de Aceite assinado** ⭐ |
| Buffer | 07/11 – 17/11 | Correção de eventuais achados de última hora, ensaio de apresentação, preparo do ambiente de demo | Ambiente de demo estável e testado | Disponível sob demanda se algo mudar |
| — | **18/11** | **Apresentação do TCC** | — | Idealmente presente/citável na defesa |

> **Regra de ouro do cronograma:** cada semana testa o módulo desenvolvido na
> semana anterior (ou já pronto). Se o desenvolvimento atrasar, o teste do módulo
> correspondente desliza junto — por isso o code freeze em 04/11 é inegociável:
> ele garante 2 dias de estabilização antes do prazo de 06/11.
>
> ⭐ = checkpoints não-negociáveis com o cliente. Confirmar essas 2 datas
> (Checkpoint 2 e UAT Final) com prioridade máxima ao agendar — são as que mais
> pesam na avaliação de "resolve o problema real" (seção 1.3).

---

## 9. Casos de Teste por Módulo

Formato padrão de caso de teste (compatível com ISTQB):

`ID | Título | Pré-condições | Passos | Resultado Esperado | Prioridade | Tipo`

### 9.0 Smoke Test (executado a cada nova build, todas as semanas)

| ID | Título | Passos | Resultado Esperado | Prioridade |
|---|---|---|---|---|
| CT-SMK-001 | API sobe e responde | `GET /` | HTTP 200, `{"status": "online"}` | P0 |
| CT-SMK-002 | Swagger/OpenAPI acessível | `GET /docs` | Página carrega sem erro | P1 |
| CT-SMK-003 | Conexão com banco ativa | Qualquer `GET` que consulte o DB | HTTP 200 (não 500) | P0 |

---

### 9.1 M1 — Usuários / Perfil

| ID | Título | Pré-condições | Passos | Resultado Esperado | Prioridade | Tipo |
|---|---|---|---|---|---|---|
| CT-USR-001 | Criar usuário com dados válidos | Banco limpo | `POST /profile` com email válido | HTTP 201, retorna `id` (UUID) e `criado_em` | P0 | Funcional |
| CT-USR-002 | Rejeitar email duplicado | Usuário já existe | `POST /profile` com mesmo email | HTTP 500/erro tratado, sem duplicar registro | P1 | Funcional/Negativo |
| CT-USR-003 | Rejeitar email em formato inválido | — | `POST /profile` com `email="abc"` | HTTP 422 (validação Pydantic) | P1 | Validação |
| CT-USR-004 | Buscar usuário por ID existente | Usuário criado (CT-USR-001) | `GET /profile/{id}` | HTTP 200, dados corretos | P0 | Funcional |
| CT-USR-005 | Buscar usuário inexistente | — | `GET /profile/{uuid_aleatorio}` | HTTP 404 | P1 | Negativo |
| CT-USR-006 | Onboarding salva preferências parciais | Usuário criado | `POST /profile/{id}/perfil` só com `objetivos_estudo` | HTTP 200, demais campos preservados (`COALESCE`) | P1 | Funcional |
| CT-USR-007 | Onboarding rejeita `estilo_preferido` fora do enum | Usuário criado | `POST /profile/{id}/perfil` com valor inválido | HTTP 422 | P2 | Validação |
| CT-USR-008 | Deletar usuário remove em cascata pastas/documentos | Usuário com pastas | `DELETE /profile/{id}` → `GET /pastas/user/{id}` | HTTP 204 na deleção; pastas do usuário não existem mais (FK `ON DELETE CASCADE`) | P0 | Integridade de dados |

---

### 9.2 M2 — Pastas e Documentos

| ID | Título | Pré-condições | Passos | Resultado Esperado | Prioridade | Tipo |
|---|---|---|---|---|---|---|
| CT-DOC-001 | Criar pasta raiz | Usuário existente | `POST /pastas` sem `pasta_pai_id` | HTTP 201 | P0 | Funcional |
| CT-DOC-002 | Criar subpasta | Pasta raiz existente | `POST /pastas` com `pasta_pai_id` válido | HTTP 201, aninhamento correto | P1 | Funcional |
| CT-DOC-003 | Upload de PDF válido | Pasta existente | `POST /documentos/upload` (multipart, PDF real) | HTTP 201, arquivo presente no bucket S3 de teste, `chave_s3` salva no banco | P0 | Funcional/Integração |
| CT-DOC-004 | Upload de arquivo não-PDF | Pasta existente | `POST /documentos/upload` com `.txt` | Comportamento definido (rejeitar ou aceitar e falhar depois na extração) — **validar e documentar o comportamento real** | P1 | Negativo |
| CT-DOC-005 | Gerar URL pré-assinada de visualização | Documento com upload concluído | `GET /documentos/{id}/url-visualizacao` | HTTP 200, URL válida por tempo limitado, acessa o PDF | P1 | Funcional |
| CT-DOC-006 | Acessar documento de outro usuário | Documento pertence ao usuário A | Usuário B chama `GET /documentos/{id}/url-visualizacao` com seu próprio `X-User-Id` | HTTP 404 (isolamento de dados) | P0 | **Segurança** |
| CT-DOC-007 | Renomear documento | Documento existente | `PUT /documentos/{id}` com novo nome | HTTP 200, nome atualizado | P2 | Funcional |
| CT-DOC-008 | Deletar pasta com documentos dentro | Pasta com documentos | `DELETE /pastas/{id}` | Definir comportamento esperado (cascata ou bloqueio) e validar | P1 | Integridade de dados |
| CT-DOC-009 | Listar conteúdo com paginação | Pasta com >50 documentos (dado de teste) | `GET /pastas/{id}/conteudo?limit=10&offset=0` | Retorna 10 itens, `tem_mais_paginas=true` | P2 | Funcional |

---

### 9.3 M3 — Resumos (Bedrock)

| ID | Título | Pré-condições | Passos | Resultado Esperado | Prioridade | Tipo |
|---|---|---|---|---|---|---|
| CT-RES-001 | Gerar resumo formato "resumo_executivo" | Documento com PDF processável | `POST /documentos/{id}/resumos` (`nivel_conhecimento=5`, `formato=resumo_executivo`, `tom="direta"`) | HTTP 201, `.md` salvo no S3, registro em `resumos` com `tokens_utilizados > 0` | P0 | Funcional/Integração IA |
| CT-RES-002 | Gerar resumo formato "cornell" | idem | idem com `formato=cornell` | Conteúdo gerado segue estrutura Cornell (tabela Pergunta\|Resposta) | P0 | Funcional/Integração IA |
| CT-RES-003 | Gerar resumo formato "fichamento_academico" | idem | idem com `formato=fichamento_academico` | Conteúdo contém citações diretas e apreciação crítica | P0 | Funcional/Integração IA |
| CT-RES-004 | `nivel_conhecimento` fora do range 0–10 | — | `POST .../resumos` com `nivel_conhecimento=15` | HTTP 422 (validação Pydantic `ge=0, le=10`) | P1 | Validação |
| CT-RES-005 | Gerar resumo para documento inexistente | — | `POST /documentos/{uuid_invalido}/resumos` | HTTP 404 | P1 | Negativo |
| CT-RES-006 | Falha do Bedrock (throttling simulado) | Mock configurado para lançar `ThrottlingException` | Chamar geração de resumo | Serviço faz retry (até 3x) e só então falha com erro tratado (não 500 cru) | P1 | Resiliência |
| CT-RES-007 | Resposta da IA não é texto válido/vazio | Mock retorna string vazia | Gerar resumo | Sistema não quebra; loga aviso; comportamento definido | P2 | Resiliência |
| CT-RES-008 | Deletar resumo | Resumo criado | `DELETE /resumos/{id}` | HTTP 204, registro removido do banco (arquivo em S3 pode ou não ser removido — **decidir e documentar**) | P2 | Funcional |
| CT-RES-009 | Múltiplos resumos para o mesmo documento | Documento existente | Gerar resumo executivo e depois cornell para o mesmo `documento_id` | Ambos coexistem (tabela `resumos` suporta N por documento) | P1 | Funcional (regra de negócio central) |

---

### 9.4 M4 — Flashcards (Bedrock + SM-2)

| ID | Título | Pré-condições | Passos | Resultado Esperado | Prioridade | Tipo |
|---|---|---|---|---|---|---|
| CT-FLC-001 | Gerar flashcards com quantidade padrão | Documento processável | `POST /documentos/{id}/flashcards` (`quantidade=10`) | HTTP 201, 10 registros em `cartoes` vinculados ao `flashcard_id`, todos com `fator_facilidade=2.5` | P0 | Funcional/Integração IA |
| CT-FLC-002 | JSON malformado retornado pela IA | Mock retorna texto não-JSON | Gerar flashcards | Exceção tratada (`ValueError` com mensagem clara), não quebra o servidor | P0 | Resiliência |
| CT-FLC-003 | `quantidade` fora do range (1–50) | — | `POST .../flashcards` com `quantidade=100` | HTTP 422 | P1 | Validação |
| CT-FLC-004 | Conteúdo JSON salvo em S3 é recuperável | Flashcard gerado | `GET` direto no S3 pela `s3_chave` retornada | JSON com `item_ref`, `pergunta`, `resposta` para cada card | P1 | Integração |
| CT-FLC-005 | Deletar flashcard remove cartões em cascata | Flashcard com cartões | `DELETE /flashcards/{id}` → checar tabela `cartoes` | HTTP 204; cartões associados removidos (FK `ON DELETE CASCADE`) | P0 | Integridade de dados |

---

### 9.5 M5 — Quizzes (Bedrock + SM-2)

Espelha M4 (mesma lógica, tabela `questoes`).

| ID | Título | Resultado Esperado | Prioridade |
|---|---|---|---|
| CT-QUI-001 | Gerar quiz com quantidade padrão | HTTP 201, N questões em `questoes`, `fator_facilidade=2.5` | P0 |
| CT-QUI-002 | Alternativa correta presente em todas as questões | Cada item do JSON tem `resposta_correta` dentre as `alternativas` | P0 |
| CT-QUI-003 | JSON malformado da IA | Erro tratado, sem 500 cru | P0 |
| CT-QUI-004 | Deletar quiz remove questões em cascata | Questões associadas removidas | P0 |

---

### 9.6 M6 — Revisão / Daily Mix (SM-2) — **Módulo Crítico**

Este é o módulo com maior peso acadêmico (algoritmo implementado do zero) e
maior risco técnico. Cobertura deve ser exaustiva, incluindo **casos de borda
matemáticos**.

| ID | Título | Pré-condições | Passos | Resultado Esperado | Prioridade | Tipo |
|---|---|---|---|---|---|---|
| CT-REV-001 | Cartão novo aparece no Daily Mix | Flashcard recém-gerado (`proxima_revisao` = agora) | `GET /revisoes/hoje` | Cartão presente na lista | P0 | Funcional |
| CT-REV-002 | Cartão futuro NÃO aparece no Daily Mix | Cartão com `proxima_revisao` = amanhã (setado manualmente no teste) | `GET /revisoes/hoje` | Cartão ausente da lista | P0 | Funcional |
| CT-REV-003 | Avaliar com qualidade=5 (acerto fácil), repetições=0 | Cartão novo, `repeticoes=0` | `PUT /revisoes/cartoes/{id}/avaliar` `{"qualidade":5}` | `intervalo_atual=1`, `repeticoes=1`, `proxima_revisao` = hoje+1 dia | P0 | **Unitário/Funcional — algoritmo** |
| CT-REV-004 | Avaliar 2ª vez com sucesso (repeticoes=1→2) | Cartão com `repeticoes=1` | `PUT .../avaliar` `{"qualidade":4}` | `intervalo_atual=6` (regra fixa da 2ª repetição) | P0 | **Unitário — algoritmo** |
| CT-REV-005 | Avaliar 3ª vez com sucesso (repeticoes=2→3) | Cartão com `repeticoes=2`, `intervalo_atual=6`, `EF=2.5` | `PUT .../avaliar` `{"qualidade":4}` | `intervalo_atual = ceil(6 * 2.5) = 15` | P0 | **Unitário — algoritmo** |
| CT-REV-006 | Reprovação zera progresso (qualidade < 3) | Cartão com `repeticoes=3` | `PUT .../avaliar` `{"qualidade":2}` | `repeticoes=0`, `intervalo_atual=1`, `proxima_revisao`=amanhã | P0 | **Unitário — algoritmo** |
| CT-REV-007 | EF nunca cai abaixo de 1.3 | Cartão com `EF=1.35`, avaliações repetidas com `qualidade=1` | Avaliar várias vezes seguidas com nota baixa | `fator_facilidade` nunca menor que `1.3` | P0 | **Unitário — regra de contorno** |
| CT-REV-008 | EF inicial de cartão novo é sempre 2.5 | Flashcard recém-gerado | Consultar `cartoes` direto no banco | Todos os registros com `fator_facilidade=2.5` | P0 | Integração |
| CT-REV-009 | Cálculo do EF segue a fórmula exata | Estado conhecido (EF, qualidade) | Chamar `SpacedRepetitionService.avaliar()` diretamente (teste unitário puro) | `EF_novo == EF_atual + (0.1 - (5-q)*(0.08+(5-q)*0.02))`, comparar com cálculo manual em planilha para 5 valores de `q` (1 a 5) | P0 | **Unitário — validação matemática** |
| CT-REV-010 | Daily Mix consolida cartões e questões | Usuário com flashcards e quizzes pendentes | `GET /revisoes/hoje` | Resposta contém `cartoes[]`, `questoes[]` e `total` correto | P0 | Funcional |
| CT-REV-011 | Conteúdo do S3 é mesclado corretamente ao item de revisão | Cartão pendente | `GET /revisoes/hoje` | Campo `conteudo` do item contém `pergunta`/`resposta` reais (não nulo) | P1 | Integração |
| CT-REV-012 | Avaliar item de outro usuário | Cartão pertence ao usuário A | Usuário B tenta `PUT /revisoes/cartoes/{id}/avaliar` | HTTP 404 (isolamento por `usuario_id` na query) | P0 | **Segurança** |
| CT-REV-013 | Avaliar com qualidade fora do range 1–5 | — | `PUT .../avaliar` `{"qualidade":7}` | HTTP 422 | P1 | Validação |
| CT-REV-014 | Performance: `GET /revisoes/hoje` com grande volume | Usuário de teste com 5.000 cartões via seed script | `GET /revisoes/hoje` | Resposta em < 500ms (índice `(usuario_id, proxima_revisao)` funcionando) | P1 | Performance |

> **Nota de rigor acadêmico:** CT-REV-003 a CT-REV-009 devem ser apresentados na
> defesa com uma tabela de cálculo manual (Excel/planilha) comparando o resultado
> esperado matematicamente vs. o resultado retornado pela API — evidência forte
> de corretude do algoritmo central do TCC.

---

### 9.7 M7 — Dashboard

| ID | Título | Resultado Esperado | Prioridade |
|---|---|---|---|
| CT-DSH-001 | Dashboard reflete contadores reais | `total_resumos`, `total_flashcards`, `total_quizzes` batem com `COUNT(*)` real no banco | P1 |
| CT-DSH-002 | Dashboard de usuário sem atividade | Listas vazias, contadores em 0 (sem erro 500) | P2 |
| CT-DSH-003 | "Últimos resumos" reflete tabela `resumos` (não a coluna legada `documentos.resumo`) | Gerar resumo novo → aparece no dashboard | P1 |

---

### 9.8 Cenário de Aceitação E2E (Golden Path)

Este é o roteiro que deve ser **ensaiado e demonstrado na apresentação**.

| Passo | Ação | Resultado Esperado |
|---|---|---|
| 1 | `POST /profile` — criar usuário de demonstração | Usuário criado |
| 2 | `POST /profile/{id}/perfil` — onboarding | Preferências salvas |
| 3 | `POST /pastas` — criar pasta "TCC Demo" | Pasta criada |
| 4 | `POST /documentos/upload` — subir PDF real (ex.: artigo acadêmico) | Documento salvo, status atualizado |
| 5 | `POST /documentos/{id}/resumos` — gerar resumo Cornell | Resumo `.md` gerado e legível |
| 6 | `POST /documentos/{id}/flashcards` — gerar 10 flashcards | 10 cartões criados, `EF=2.5` |
| 7 | `GET /revisoes/hoje` | Os 10 cartões aparecem pendentes |
| 8 | `PUT /revisoes/cartoes/{id}/avaliar` (qualidade=5) em 3 cartões | `proxima_revisao` avança corretamente para cada um |
| 9 | `GET /revisoes/hoje` novamente | Os 3 cartões avaliados não aparecem mais (foram para o futuro); os 7 restantes continuam |
| 10 | `GET /profile/{id}/dashboard` | Contadores refletem o resumo e o flashcard criados |

**Critério de aceite do cenário:** todos os 10 passos executam sem erro, na
ordem, usando a API real (não mockada) em ambiente de homologação.

---

### 9.9 Roteiro de UAT Final (Semana 9, com o cliente)

Diferente do cenário 9.8 (que eu executo, chamando a API), o UAT Final é
**operado pelo cliente**, com uma interface mínima (Swagger `/docs`, Postman, ou
o frontend se já existir). Eu apenas guio e observo — não digito por ele.

**Roteiro (adaptar a linguagem para o domínio do cliente, não usar termos como
"endpoint" ou "payload" na frente dele):**

| Tarefa dada ao cliente | O que estou observando |
|---|---|
| "Suba um material seu (PDF) que você usaria de verdade" | Ele entende o fluxo sem ajuda? Onde hesita? |
| "Peça um resumo desse material, no formato que fizer mais sentido pra você" | Ele entende a diferença entre os 3 formatos (executivo/cornell/fichamento)? A explicação da IA é clara? |
| "Avalie: esse resumo te ajudaria de verdade a estudar/revisar esse conteúdo?" | Resposta qualitativa — registrar literalmente |
| "Gere um conjunto de flashcards a partir do mesmo material" | Ele reconhece valor no conteúdo gerado (não genérico demais)? |
| "Agora revise 3 ou 4 desses flashcards, como se fosse seu estudo do dia" | Ele entende o conceito de repetição espaçada sem eu explicar o algoritmo? |
| "O que faltou? O que você mudaria?" | Pergunta aberta final — insumo principal para os "Trabalhos Futuros" do TCC |

**Ao final da sessão:**
1. Consolidar achados novos como `UAT-XXX` (modelo da seção 3.3.1).
2. Revisar, junto com o cliente, todos os achados de UAT abertos desde os
   checkpoints anteriores (S1, S3, S5, S7) — cada um precisa de uma decisão.
3. Preencher e assinar o **Termo de Aceite** abaixo.

#### Termo de Aceite (modelo)

> Eu, **\[nome do cliente]**, representando **\[organização, se aplicável]**,
> declaro que participei das sessões de validação do sistema **Bright EdTech**
> nas datas **\[listar]**, e que na sessão final de **\[06/11/2026]** pude operar
> as funcionalidades de upload de material, geração de resumos, geração de
> flashcards e revisão espaçada.
>
> ☐ Confirmo que o sistema, no estado apresentado, atende à necessidade que
> motivou este projeto.
> ☐ Confirmo com ressalvas — os pontos pendentes estão registrados nos achados
> de UAT anexos a este documento (`UAT-___` a `UAT-___`), com decisão explícita
> sobre cada um.
>
> Assinatura: ________________________ Data: __/__/____

> Anexar este termo (preenchido e assinado — pode ser digital, ex.: e-mail de
> confirmação, se assinatura física não for viável) como apêndice do TCC. É a
> evidência mais forte de que a exigência do IFSP (cliente real) foi cumprida
> com rigor, não apenas mencionada em texto.

---

## 10. Matriz de Rastreabilidade (Requisito → Teste)

| Requisito (funcionalidade) | Módulo | Casos de Teste | Status |
|---|---|---|---|
| Cadastro e onboarding sem verificação obrigatória (soft gating) | M1 | CT-USR-001, 006 | ⬜ Pendente |
| Isolamento de dados por usuário | M2, M6 | CT-DOC-006, CT-REV-012 | ⬜ Pendente |
| Upload de PDF para S3 | M2 | CT-DOC-003 | ⬜ Pendente |
| Geração de resumo em 3 formatos via IA | M3 | CT-RES-001–003, 009 | ⬜ Pendente |
| Resiliência a falhas do provedor de IA | M3, M4, M5 | CT-RES-006/007, CT-FLC-002, CT-QUI-003 | ⬜ Pendente |
| Geração de flashcards/quizzes com estado SM-2 inicial | M4, M5 | CT-FLC-001, CT-QUI-001 | ⬜ Pendente |
| Algoritmo SM-2 correto (fórmula e regras de contorno) | M6 | CT-REV-003–009 | ⬜ Pendente |
| Fila de revisão diária (Daily Mix) | M6 | CT-REV-001, 002, 010, 011 | ⬜ Pendente |
| Performance da consulta de revisão | M6 | CT-REV-014 | ⬜ Pendente |
| Dashboard consolidado | M7 | CT-DSH-001–003 | ⬜ Pendente |
| Jornada completa do usuário | Todos | CT-E2E (seção 9.8) | ⬜ Pendente |
| Sistema atende à necessidade real do cliente | Todos | UAT — Checkpoints 1/2/3 + UAT Final (seção 9.9) | ⬜ Pendente |

> Atualizar a coluna **Status** (⬜ Pendente / 🟡 Em execução / ✅ Aprovado / ❌
> Reprovado) semanalmente conforme o cronograma da seção 8. Esta tabela é o
> principal artefato de evidência a apresentar à banca.

---

## 11. Gestão de Defeitos

### 11.1 Severidade (impacto técnico)

| Nível | Definição | Exemplo |
|---|---|---|
| **Crítica** | Sistema indisponível ou perda/corrupção de dados | `DELETE /profile/{id}` não remove documentos em cascata, deixando dados órfãos |
| **Alta** | Funcionalidade principal não funciona | Geração de resumo retorna erro 500 sempre |
| **Média** | Funcionalidade secundária afetada, existe contorno | Paginação retorna `tem_mais_paginas` errado |
| **Baixa** | Cosmético, não afeta uso | Mensagem de erro com texto impreciso |

### 11.2 Prioridade (urgência de correção)

`P0` (corrigir imediatamente) · `P1` (corrigir na semana corrente) · `P2` (corrigir
até o code freeze) · `P3` (backlog pós-TCC)

### 11.3 Fluxo

```
Aberto → Em análise → Em correção → Em reteste → Fechado
                                   ↘ Reaberto (se reteste falhar)
```

Registrar cada defeito como GitHub Issue com labels `bug`, `severidade:*`,
`prioridade:*`, `modulo:M1..M8`. Isso gera, por si só, um relatório de qualidade
apresentável (gráfico de burndown de bugs) direto do GitHub.

---

## 12. Testes Não-Funcionais (M8)

| ID | Categoria | Teste | Meta | Ferramenta |
|---|---|---|---|---|
| CT-NFR-001 | Performance | Latência de `GET /revisoes/hoje` com 5.000 cartões | p95 < 500ms | `locust` |
| CT-NFR-002 | Performance | Tempo de geração de resumo (fim a fim, incluindo chamada Bedrock) | < 30s para PDF de 10 páginas | Medição manual/log |
| CT-NFR-003 | Segurança | Requisição sem header `X-User-Id` em rota protegida | HTTP 401 | Postman |
| CT-NFR-004 | Segurança | Header `X-User-Id` malformado (não-UUID) | HTTP 400 | Postman |
| CT-NFR-005 | Segurança | Usuário A não acessa/edita/deleta recursos do usuário B | HTTP 404 em todas as tentativas (ver CT-DOC-006, CT-REV-012) | Postman |
| CT-NFR-006 | Integridade | Exclusão de usuário limpa 100% dos dados relacionados (LGPD-friendly) | Nenhum registro órfão em nenhuma tabela | Query SQL manual pós-teste |
| CT-NFR-007 | Confiabilidade | API se recupera de indisponibilidade momentânea do Bedrock (retry) | Retry automático até 3x, erro tratado ao esgotar | Mock com falha simulada |
| CT-NFR-008 | Usabilidade da API | Documentação OpenAPI (`/docs`) reflete corretamente todos os endpoints e schemas | 100% dos endpoints documentados com exemplos | Inspeção manual do Swagger |

---

## 13. Métricas de Qualidade (para reportar na defesa)

| Métrica | Meta | Como medir |
|---|---|---|
| Cobertura de testes unitários (regras de negócio) | ≥ 80% | `pytest --cov=app` |
| % de casos de teste P0 aprovados | 100% | Matriz de rastreabilidade (seção 10) |
| % de casos de teste P1 aprovados | ≥ 90% | idem |
| Defeitos críticos/altos abertos na data de corte (06/11) | 0 | GitHub Issues |
| Taxa de sucesso do cenário E2E (seção 9.8) em execuções consecutivas | 100% (mín. 3 execuções) | Log de execução |
| Tempo de resposta do Daily Mix (p95) | < 500ms | `locust` |

---

## 14. Riscos do Plano de Testes

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Dependência de custo/quota do Bedrock atrasa testes de M3/M4/M5 | Média | Alto | Usar mocks (`unittest.mock`) para a maioria dos casos; reservar poucas chamadas reais para validação de integração verdadeira |
| Cronograma pessoal (TCC solo) sofre atraso em alguma semana | Média | Alto | Buffer de 12 dias (07/11–17/11) já reservado; se um módulo atrasar, reduzir escopo de P2/P3 antes de mexer no code freeze |
| Ambiente de homologação divergir do ambiente de demo no dia 18/11 | Baixa | Alto | Congelar ambiente de demo em 10/11 e não tocar mais nele, apenas no `local`/`homologação` |
| Algoritmo SM-2 apresentar bug sutil não coberto pelos testes de borda | Baixa | Alto (é o diferencial do TCC) | Validação cruzada manual em planilha (nota da seção 9.6) antes de fechar M6 |
| Falta de dados de teste realistas (PDFs variados) | Média | Médio | Preparar um conjunto de 3–5 PDFs de tamanhos/temas diferentes já na Semana 1 |

**Trabalho futuro (fora do escopo deste plano, mencionar na defesa se perguntado):**
testes de carga em escala de produção, penetration testing formal, testes de
frontend, cache Redis e sharding de tabelas de revisão (decisões já documentadas
em `.context/referencia-rapida.md`).

---

## 15. Marcos (Milestones)

| Data | Marco |
|---|---|
| 09/09/2026 | Plano de testes aprovado, ambiente de testes pronto |
| 09/09/2026 | **Kickoff de validação com o cliente** — escopo confirmado |
| 22/09/2026 | M1 concluído |
| 29/09/2026 | M2 concluído + **Checkpoint 1 com o cliente** |
| 06/10/2026 | M3 concluído |
| 13/10/2026 | M4 e M5 concluídos + **Checkpoint 2 com o cliente** (qualidade do conteúdo IA) ⭐ |
| 20/10/2026 | M6 (SM-2) concluído — **marco crítico** |
| 27/10/2026 | M7 concluído + 1ª execução E2E + **Checkpoint 3 com o cliente** |
| 03/11/2026 | M8 (não-funcionais) concluído + regressão geral |
| **06/11/2026** | **Code freeze — todos os módulos com critério de saída atingido + UAT Final e Termo de Aceite assinado (Go/No-Go)** ⭐ |
| 17/11/2026 | Ambiente de demo validado, ensaio de apresentação concluído |
| **18/11/2026** | **Apresentação do TCC** |

---

## 16. Aprovação

| Papel | Nome | Data | Assinatura/De acordo |
|---|---|---|---|
| Autor do Plano | Eric Ferreira Martins | 09/09/2026 | |
| Orientador(a) | | | |
| Cliente Real | | | *(via Termo de Aceite, seção 9.9)* |

---

*Este documento é um artefato vivo: atualizar o status da matriz de
rastreabilidade (seção 10) semanalmente conforme o cronograma (seção 8)
avança. Ver também [`referencia-rapida.md`](referencia-rapida.md) para os
endpoints reais e [`dados.md`](dados.md) para o schema.*
