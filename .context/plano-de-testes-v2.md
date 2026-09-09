# Plano de Testes — Bright EdTech 

| | |
|---|---|
| **Projeto** | Bright EdTech — Plataforma SaaS de aprendizagem ativa com IA |
| **Trabalho** | TCC — IFSP, Análise e Desenvolvimento de Sistemas |
| **Documento** | Plano de Testes |
| **Autores** | Eric , Gabriela, Miguel, João |
| **Data de elaboração** | 09/09/2026 |
| **Prazo final de testes** | 06/11/2026 |
| **Apresentação do TCC** | 18/11/2026 |

---

## 1. Introdução

### 1.1 Objetivo

Definir o que será testado, como, quando, e o que caracteriza "pronto" — para o
Bright EdTech (backend + frontend) chegar em 06/11/2026 funcionando de ponta a
ponta e validado por um cliente real, com folga até a apresentação em 18/11.

### 1.2 Contexto

Bright EdTech gera Resumos, Flashcards e Quizzes via IA (Amazon Bedrock) a
partir de PDFs, e gerencia retenção via repetição espaçada (SM-2).



### 1.3 Escopo

**Dentro do escopo:** API REST completa (todos os módulos da seção 2),
integração com Bedrock e S3, banco PostgreSQL, algoritmo SM-2, e o **frontend**
nas telas que consomem esses módulos (M9, seção 2).


**Fora do escopo:** testes automatizados de UI (Cypress/Playwright), testes de
carga em escala de produção, penetration testing formal, cache Redis.

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
| M8 | **Não-funcionais** | Performance e segurança básica (isolamento de dados) | Transversal |
| M9 | **Frontend (Interface)** | Telas que consomem os módulos acima: onboarding, Document Hub (PDF + abas), Daily Mix | React SPA (repositório separado do frontend) |

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

| Nível | Ferramenta | O que cobre | Meta |
|---|---|---|---|
| **Unitário** | `pytest` | Regras de negócio puras (ex.: `SpacedRepetitionService`, validação de Pydantic schemas) | ≥ 80% nas regras críticas |
| **Integração** | `pytest` + Postgres de teste (Docker) + mocks de S3/Bedrock (`moto`, `unittest.mock`) | Repository ↔ Banco real; Service ↔ Repository | Todos os fluxos críticos |
| **Sistema / API** | `pytest` + `httpx.AsyncClient` / Postman-Newman | Endpoints FastAPI ponta a ponta | 100% dos endpoints públicos |
| **Aceitação técnica (E2E)** | Roteiro manual + Postman Collection | Jornada completa do usuário | Cenário da seção 6.8 |
| **Frontend (manual/exploratório)** | Checklist por tela, navegador real | UI reflete corretamente a API (M9) | Seção 6.10 — sem meta de cobertura, é checklist |
| **Aceitação do Cliente (UAT)** | Sessões guiadas | O sistema resolve o problema real do cliente | Seção 3.3 e 6.9 |

> O frontend não tem nível de teste automatizado dedicado neste ciclo — ele é
> validado manualmente (6.10) e, principalmente, pelo próprio cliente nos
> checkpoints de UAT, que já usam a interface real quando disponível.

### 3.2 Abordagem Baseada em Risco

| Módulo | Probabilidade de falha | Impacto se falhar | Prioridade |
|---|---|---|---|
| M6 — SM-2 (Revisão) | Média (matemática + estado) | **Alto** (core do produto) | 🔴 **P0** |
| M3/M4/M5 — Geração via IA | Alta (dependência externa, parsing de JSON) | Alto | 🔴 **P0** |
| M2 — Documentos/S3 | Média (I/O externo) | Alto | 🟠 **P1** |
| M1 — Usuários/Perfil | Baixa (CRUD simples) | Médio | 🟡 **P2** |
| M7 — Dashboard | Baixa | Baixo | 🟢 **P3** |
| M8 — Não-funcionais | Média | Médio | 🟠 **P1** |
| M9 — Frontend | Média (integração com API em paralelo) | Médio (afeta percepção do cliente, não os dados) | 🟡 **P2** |

### 3.3 Testes de Aceitação com o Cliente (UAT)

Não valida "o código funciona" — valida "isso é o que o cliente precisava".
Conduzido **com o cliente presente**, sobre o ambiente de homologação, na
linguagem dele (sem jargão técnico).

**Formato de cada sessão:**
1. Demonstro a funcionalidade pronta (10 min).
2. Cliente opera sozinho, com tarefas guiadas, não passo a passo (15–20 min).
3. Coleto feedback estruturado.
4. Registro cada item como **Achado de UAT**, com uma decisão explícita
   (ajustar agora / ajustar até 06/11 / melhoria futura / aceitar como está).


#### Modelo de Registro de Achado de UAT

| Campo | Descrição |
|---|---|
| ID | `UAT-XXX` |
| Checkpoint | Qual sessão gerou o achado |
| Módulo | M1–M8 |
| Relato do cliente | Na linguagem dele |
| Interpretação técnica | O que isso significa em termos de código/fluxo |
| Decisão | Ajustar agora / até 06/11 / futuro / aceitar como está |
| Status | Aberto / Em tratamento / Resolvido / Adiado |

---

## 4. Critérios de Entrada e Saída

### 4.1 Entrada (para iniciar os testes de um módulo)
- Código do módulo mergeado e compilando sem erros.
- `schema.sql` aplicado no ambiente de testes.
- `.env` configurado (Bedrock, S3, DB).
- Casos de teste do módulo revisados (seção 6).

### 4.2 Saída (para considerar um módulo "testado")
- 100% dos casos **P0/P1** executados.
- Zero defeitos abertos com severidade Crítica ou Alta.
- Cobertura de teste unitário ≥ 80% nas classes de serviço do módulo.
- Evidência (print/log/relatório do pytest) anexada à matriz (seção 8).

### 4.3 Saída Geral do Projeto (Go/No-Go para 18/11)
- Todos os módulos M1–M8 com critério de saída (4.2) atingido até **06/11**.
- Checklist do frontend (M9, seção 6.10) executado em todas as telas — 100%
  ✅ ou com achados documentados e decisão registrada (não precisa ser
  perfeito, precisa estar **decidido**).
- Cenário E2E (seção 6.8) executado com sucesso 3 vezes consecutivas.
- Zero defeitos Crítico/Alto em aberto na data de corte.
- **UAT Final realizada e Termo de Aceite assinado** (seção 6.9) — sem isso,
  não há Go, mesmo com os testes técnicos 100% verdes.

---

## 5. Ambiente de Testes

| Ambiente | Finalidade | Observação |
|---|---|---|
| **Local (dev)** | Testes unitários/integração no dia a dia | Postgres via Docker, bucket S3 de teste |
| **Homologação** | Ensaio geral, UAT | Schema real, dados sintéticos |
| **Demo (apresentação)** | Ambiente estável para a banca em 18/11 | Congelado a partir de 10/11 |

### 5.1 Ferramentas

| Categoria | Ferramenta |
|---|---|
| Testes unitários/integração | `pytest`, `pytest-cov`, `pytest-asyncio` |
| Mock de AWS | `moto` (S3) / `unittest.mock` (Bedrock) |
| Testes de API | `httpx`, Postman |
| Banco de testes | PostgreSQL  |

---

## 6. Casos de Teste por Módulo

Formato: `ID | Título | Pré-condições | Passos | Resultado Esperado | Prioridade`

### 6.0 Smoke Test

| ID | Título | Passos | Resultado Esperado | Prioridade |
|---|---|---|---|---|
| CT-SMK-001 | API sobe e responde | `GET /` | HTTP 200, `{"status": "online"}` | P0 |
| CT-SMK-002 | Swagger acessível | `GET /docs` | Página carrega sem erro | P1 |
| CT-SMK-003 | Conexão com banco ativa | Qualquer `GET` que consulte o DB | HTTP 200 (não 500) | P0 |

### 6.1 M1 — Usuários / Perfil

| ID | Título | Passos | Resultado Esperado | Prioridade |
|---|---|---|---|---|
| CT-USR-001 | Criar usuário com dados válidos | `POST /profile` com email válido | HTTP 201, retorna `id` e `criado_em` | P0 |
| CT-USR-002 | Rejeitar email duplicado | `POST /profile` com email já existente | Erro tratado, sem duplicar registro | P1 |
| CT-USR-003 | Rejeitar email inválido | `POST /profile` com `email="abc"` | HTTP 422 | P1 |
| CT-USR-004 | Buscar usuário por ID | `GET /profile/{id}` | HTTP 200, dados corretos | P0 |
| CT-USR-005 | Buscar usuário inexistente | `GET /profile/{uuid_aleatorio}` | HTTP 404 | P1 |
| CT-USR-006 | Onboarding salva preferências parciais | `POST /profile/{id}/perfil` só com `objetivos_estudo` | HTTP 200, demais campos preservados | P1 |
| CT-USR-007 | Onboarding rejeita valor fora do enum | `POST /profile/{id}/perfil` com `estilo_preferido` inválido | HTTP 422 | P2 |
| CT-USR-008 | Deletar usuário remove pastas/documentos em cascata | `DELETE /profile/{id}` → `GET /pastas/user/{id}` | HTTP 204 na deleção; nada retorna depois | P0 |

### 6.2 M2 — Pastas e Documentos

| ID | Título | Passos | Resultado Esperado | Prioridade |
|---|---|---|---|---|
| CT-DOC-001 | Criar pasta raiz | `POST /pastas` sem `pasta_pai_id` | HTTP 201 | P0 |
| CT-DOC-002 | Criar subpasta | `POST /pastas` com `pasta_pai_id` válido | HTTP 201, aninhamento correto | P1 |
| CT-DOC-003 | Upload de PDF válido | `POST /documentos/upload` (multipart, PDF real) | HTTP 201, arquivo no S3 de teste, `chave_s3` salva | P0 |
| CT-DOC-004 | Upload de arquivo não-PDF | `POST /documentos/upload` com `.txt` | Comportamento definido e documentado | P1 |
| CT-DOC-005 | Gerar URL pré-assinada | `GET /documentos/{id}/url-visualizacao` | HTTP 200, URL acessa o PDF | P1 |
| CT-DOC-006 | Acessar documento de outro usuário | Usuário B pede documento do usuário A | HTTP 404 (isolamento) | P0 |
| CT-DOC-007 | Renomear documento | `PUT /documentos/{id}` | HTTP 200, nome atualizado | P2 |
| CT-DOC-008 | Deletar pasta com documentos dentro | `DELETE /pastas/{id}` | Comportamento validado (cascata ou bloqueio) | P1 |

### 6.3 M3 — Resumos (Bedrock)

| ID | Título | Passos | Resultado Esperado | Prioridade |
|---|---|---|---|---|
| CT-RES-001 | Gerar resumo "resumo_executivo" | `POST /documentos/{id}/resumos` | HTTP 201, `.md` no S3, registro com `tokens_utilizados > 0` | P0 |
| CT-RES-002 | Gerar resumo "cornell" | idem com `formato=cornell` | Conteúdo em estrutura Pergunta\|Resposta | P0 |
| CT-RES-003 | Gerar resumo "fichamento_academico" | idem | Conteúdo com citações diretas | P0 |
| CT-RES-004 | `nivel_conhecimento` fora do range 0–10 | `POST .../resumos` com `nivel_conhecimento=15` | HTTP 422 | P1 |
| CT-RES-005 | Documento inexistente | `POST /documentos/{uuid_invalido}/resumos` | HTTP 404 | P1 |
| CT-RES-006 | Falha do Bedrock (throttling simulado) | Mock lança `ThrottlingException` | Retry até 3x, erro tratado (não 500 cru) | P1 |
| CT-RES-007 | Múltiplos resumos no mesmo documento | Gerar executivo e depois cornell | Ambos coexistem (tabela `resumos` suporta N por doc) | P1 |

### 6.4 M4 — Flashcards (Bedrock + SM-2)

| ID | Título | Passos | Resultado Esperado | Prioridade |
|---|---|---|---|---|
| CT-FLC-001 | Gerar flashcards (quantidade padrão) | `POST /documentos/{id}/flashcards` | HTTP 201, N cartões criados, todos com `fator_facilidade=2.5` | P0 |
| CT-FLC-002 | JSON malformado retornado pela IA | Mock retorna texto não-JSON | Exceção tratada, sem quebrar o servidor | P0 |
| CT-FLC-003 | `quantidade` fora do range | `POST .../flashcards` com `quantidade=100` | HTTP 422 | P1 |
| CT-FLC-004 | Deletar flashcard remove cartões em cascata | `DELETE /flashcards/{id}` | HTTP 204, cartões associados removidos | P0 |

### 6.5 M5 — Quizzes (Bedrock + SM-2)

| ID | Título | Resultado Esperado | Prioridade |
|---|---|---|---|
| CT-QUI-001 | Gerar quiz (quantidade padrão) | HTTP 201, N questões, `fator_facilidade=2.5` | P0 |
| CT-QUI-002 | Resposta correta presente em todas as questões | Cada item tem `resposta_correta` dentre as alternativas | P0 |
| CT-QUI-003 | JSON malformado da IA | Erro tratado, sem 500 cru | P0 |
| CT-QUI-004 | Deletar quiz remove questões em cascata | Questões associadas removidas | P0 |

### 6.6 M6 — Revisão / Daily Mix (SM-2) — módulo crítico

| ID | Título | Pré-condições | Passos | Resultado Esperado | Prioridade |
|---|---|---|---|---|---|
| CT-REV-001 | Cartão novo aparece no Daily Mix | `proxima_revisao` = agora | `GET /revisoes/hoje` | Cartão presente | P0 |
| CT-REV-002 | Cartão futuro não aparece | `proxima_revisao` = amanhã | `GET /revisoes/hoje` | Cartão ausente | P0 |
| CT-REV-003 | Avaliar qualidade=5, repetições=0 | Cartão novo | `PUT .../avaliar` `{"qualidade":5}` | `intervalo_atual=1`, `repeticoes=1` | P0 |
| CT-REV-004 | Avaliar 2ª vez com sucesso (repeticoes 1→2) | `repeticoes=1` | `PUT .../avaliar` `{"qualidade":4}` | `intervalo_atual=6` | P0 |
| CT-REV-005 | Avaliar 3ª vez (repeticoes 2→3) | `repeticoes=2`, `intervalo=6`, `EF=2.5` | `PUT .../avaliar` `{"qualidade":4}` | `intervalo = ceil(6*2.5) = 15` | P0 |
| CT-REV-006 | Reprovação zera progresso (q<3) | `repeticoes=3` | `PUT .../avaliar` `{"qualidade":2}` | `repeticoes=0`, `intervalo=1` | P0 |
| CT-REV-007 | EF nunca cai abaixo de 1.3 | `EF=1.35` | Avaliar repetidamente com `qualidade=1` | `fator_facilidade` nunca < 1.3 | P0 |
| CT-REV-008 | EF inicial sempre 2.5 | Flashcard recém-gerado | Consultar `cartoes` no banco | Todos com `fator_facilidade=2.5` | P0 |
| CT-REV-009 | Fórmula do EF confere com cálculo manual | Estado conhecido (EF, q) | Chamar `SpacedRepetitionService.avaliar()` (teste unitário) | Resultado bate com cálculo em planilha, para q de 1 a 5 | P0 |
| CT-REV-010 | Daily Mix consolida cartões e questões | Usuário com ambos pendentes | `GET /revisoes/hoje` | Resposta com `cartoes[]`, `questoes[]`, `total` correto | P0 |
| CT-REV-011 | Avaliar item de outro usuário | Cartão do usuário A | Usuário B tenta avaliar | HTTP 404 (isolamento) | P0 |
| CT-REV-012 | Avaliar com qualidade fora de 1–5 | — | `PUT .../avaliar` `{"qualidade":7}` | HTTP 422 | P1 |



### 6.7 M7 — Dashboard

| ID | Título | Resultado Esperado | Prioridade |
|---|---|---|---|
| CT-DSH-001 | Contadores batem com o banco | `total_resumos/flashcards/quizzes` = `COUNT(*)` real | P1 |
| CT-DSH-002 | Dashboard de usuário sem atividade | Listas vazias, contadores em 0, sem erro 500 | P2 |

### 6.8 Cenário de Aceitação E2E (Golden Path)

Roteiro a ser **ensaiado e demonstrado na apresentação**.

| Passo | Ação | Resultado Esperado |
|---|---|---|
| 1 | `POST /profile` — criar usuário de demonstração | Usuário criado |
| 2 | `POST /profile/{id}/perfil` — onboarding | Preferências salvas |
| 3 | `POST /pastas` — criar pasta "TCC Demo" | Pasta criada |
| 4 | `POST /documentos/upload` — subir PDF real | Documento salvo |
| 5 | `POST /documentos/{id}/resumos` — gerar resumo Cornell | Resumo `.md` gerado e legível |
| 6 | `POST /documentos/{id}/flashcards` — gerar 10 flashcards | 10 cartões, `EF=2.5` |
| 7 | `GET /revisoes/hoje` | Os 10 cartões aparecem pendentes |
| 8 | `PUT /revisoes/cartoes/{id}/avaliar` (qualidade=5) em 3 cartões | `proxima_revisao` avança corretamente |
| 9 | `GET /revisoes/hoje` novamente | Os 3 avaliados não aparecem mais |
| 10 | `GET /profile/{id}/dashboard` | Contadores refletem o criado |

**Critério de aceite:** os 10 passos executam sem erro, na ordem, com API real.
Quando o frontend estiver pronto (a partir de S7), repetir o mesmo roteiro
**pela interface**, não só via API — é o sinal de que a integração front↔back
está completa.

### 6.9 Roteiro de UAT Final (Semana 9, com o cliente)

Operado **pelo cliente**, preferencialmente pelo **frontend** 
| Tarefa dada ao cliente | O que observo |
|---|---|
| "Suba um material seu (PDF) que você usaria de verdade" | Ele entende o fluxo sem ajuda? |
| "Peça um resumo, no formato que fizer mais sentido pra você" | Ele entende a diferença entre os 3 formatos? |
| "Esse resumo te ajudaria de verdade a estudar/revisar?" | Resposta qualitativa — registrar literalmente |
| "Gere flashcards a partir do mesmo material" | Reconhece valor no conteúdo (não genérico)? |
| "Revise 3-4 desses flashcards, como seu estudo do dia" | Entende repetição espaçada sem eu explicar o algoritmo? |
| "O que faltou? O que você mudaria?" | Insumo para "Trabalhos Futuros" do TCC |

**Ao final:** consolidar achados como `UAT-XXX`, revisar achados anteriores em
aberto, e preencher o **Termo de Aceite**:

> Eu, **\[nome do cliente]**, participei das sessões de validação do Bright
> EdTech e, na sessão final de **06/11/2026**, pude operar upload de material,
> geração de resumos, flashcards e revisão espaçada.
>
> ☐ Confirmo que o sistema atende à necessidade que motivou este projeto.
> ☐ Confirmo com ressalvas — pontos pendentes registrados em `UAT-___` a
> `UAT-___`, com decisão explícita sobre cada um.
>
> Assinatura: ________________________ Data: __/__/____

### 6.10 Frontend — Checklist Manual por Tela (M9)

Leve, exploratório, sem ID formal — marcar ✅/❌ por tela a cada semana em que
ela estiver pronta (ver coluna 🖥️ no cronograma). Objetivo: pegar quebras
óbvias de integração, não validar regra de negócio (isso é do backend).

| Tela | Checklist |
|---|---|
| **Onboarding** | Formulário salva e reflete em `GET /profile/{id}`? Campos opcionais realmente são opcionais? |
| **Pastas / árvore de diretórios** | Criar/renomear/excluir pasta reflete na hora? Aninhamento aparece correto? |
| **Upload de documento** | Upload de PDF real funciona? Estado "processando → pronto" é visível? Erro de upload é comunicado ao usuário (não só um 500 silencioso)? |
| **Document Hub** (PDF + abas Resumos/Flashcards/Quizzes) | PDF renderiza? As 3 abas carregam o conteúdo certo do documento certo? |
| **Geração de Resumo** | Os 3 formatos aparecem como opção? Resultado gerado é legível na tela (não JSON cru)? Loading state existe (chamada à IA não é instantânea)? |
| **Flashcards / Quizzes gerados** | Cartões/questões renderizam a partir do JSON do S3? Nenhum item aparece em branco? |
| **Daily Mix / Túnel de Foco** | Itens pendentes de hoje aparecem? Avaliar um item (1-5) remove ele da lista corretamente? |
| **Dashboard** | Contadores na tela batem com os dados reais (comparar com resposta da API)? |
| **Responsividade básica** | Telas principais não quebram em uma resolução menor (ex.: notebook 1366px)? |



---

## 7. Cronograma

Semanal, de **09/09/2026** (hoje) até **06/11/2026** (prazo final).
| Semana | Período | Módulo(s) em foco | Entregável | 🖥️ Frontend (M9, leve) | 👤 Cliente |
|---|---|---|---|---|---|
| S1 | 09/09 – 15/09 | Setup: ambiente de testes, banco Docker, mocks de Bedrock/S3 | Ambiente pronto | Alinhar quais telas nascem em qual semana (mapear com o time de front) | **Kickoff de validação** |
| S2 | 16/09 – 22/09 | **M1 — Usuários/Perfil** | CT-USR-* executados | Checklist: Onboarding | — |
| S3 | 23/09 – 29/09 | **M2 — Pastas e Documentos** | CT-DOC-* executados | Checklist: Pastas + Upload | **Checkpoint 1** |
| S4 | 30/09 – 06/10 | **M3 — Resumos (Bedrock)** | CT-RES-* executados | Checklist: Document Hub + tela de Resumo | — |
| S5 | 07/10 – 13/10 | **M4 + M5 — Flashcards e Quizzes** | CT-FLC-*, CT-QUI-* executados | Checklist: telas de Flashcards/Quizzes | **Checkpoint 2** ⭐ (qualidade do conteúdo IA) |
| S6 | 14/10 – 20/10 | **M6 — Revisão / SM-2 (crítico)** | CT-REV-* executados | Checklist: Daily Mix / Túnel de Foco | — |
| S7 | 21/10 – 27/10 | **M7 — Dashboard** + Integração E2E | Cenário 6.8 executado 1ª vez (via API e via UI) | Checklist: Dashboard + responsividade | **Checkpoint 3** |
| S8 | 28/10 – 03/11 | Não-funcionais (M8) + regressão geral | Relatório de performance/segurança | Reteste geral de todas as telas (regressão leve) | Consolidar achados de UAT pendentes |
| S9 | 04/11 – 06/11 | **Code freeze**, smoke final, homologação, Go/No-Go | Relatório final assinado | Checklist final 100% ✅ ou achados documentados | **UAT Final + Termo de Aceite** ⭐ |
| Buffer | 07/11 – 17/11 | Correções finais, ensaio de apresentação | Ambiente de demo estável | Ajustes visuais/cosméticos de última hora | Sob demanda |
| — | **18/11** | **Apresentação do TCC** | — | — | — |


### 7.1 Disponibilidade do Cliente

Agendar já na Semana 1, **4 encontros fixos** (podem ser remotos, 30–45 min):

| Encontro | Semana | Objetivo |
|---|---|---|
| Kickoff | S1 | Confirmar escopo e expectativa de uso |
| Checkpoint 1 | S3 | Validar organização de pastas/documentos e upload |
| Checkpoint 2 | S5 | Validar **qualidade do conteúdo gerado pela IA** |
| Checkpoint 3 | S7 | Validar o fluxo de revisão diária |
| UAT Final | S9 | Roteiro completo (6.9) + assinatura do termo |



---

## 8. Matriz de Rastreabilidade (Requisito → Teste)

| Requisito | Módulo | Casos de Teste | Status |
|---|---|---|---|
| Cadastro e onboarding sem verificação obrigatória | M1 | CT-USR-001, 006 | ⬜ Pendente |
| Isolamento de dados por usuário | M2, M6 | CT-DOC-006, CT-REV-011 | ⬜ Pendente |
| Upload de PDF para S3 | M2 | CT-DOC-003 | ⬜ Pendente |
| Geração de resumo em 3 formatos via IA | M3 | CT-RES-001–003, 007 | ⬜ Pendente |
| Resiliência a falhas do provedor de IA | M3, M4, M5 | CT-RES-006, CT-FLC-002, CT-QUI-003 | ⬜ Pendente |
| Geração de flashcards/quizzes com estado SM-2 inicial | M4, M5 | CT-FLC-001, CT-QUI-001 | ⬜ Pendente |
| Algoritmo SM-2 correto | M6 | CT-REV-003–009 | ⬜ Pendente |
| Fila de revisão diária (Daily Mix) | M6 | CT-REV-001, 002, 010 | ⬜ Pendente |
| Dashboard consolidado | M7 | CT-DSH-001, 002 | ⬜ Pendente |
| Jornada completa do usuário | Todos | Cenário E2E (6.8) | ⬜ Pendente |
| Interface reflete corretamente o backend | M9 | Checklist 6.10 | ⬜ Pendente |
| Sistema atende à necessidade real do cliente | Todos | UAT (Checkpoints + Final, 6.9) | ⬜ Pendente |

> Atualizar a coluna **Status** (⬜ Pendente / 🟡 Em execução / ✅ Aprovado / ❌
> Reprovado) semanalmente. Esta tabela é o principal artefato de evidência.

---

## 9. Métricas de Qualidade

| Métrica | Meta | Como medir |
|---|---|---|
| Cobertura de testes unitários (regras de negócio) | ≥ 80% | `pytest --cov=app` |
| % de casos P0 aprovados | 100% | Matriz (seção 8) |
| % de casos P1 aprovados | ≥ 90% | idem |
| Defeitos críticos/altos abertos em 06/11 | 0 | GitHub Issues |
| Taxa de sucesso do cenário E2E em execuções consecutivas | 100% (mín. 3x) | Log de execução |

---

## 10. Marcos

| Data | Marco |
|---|---|
| 09/09/2026 | Plano de testes pronto, ambiente de testes pronto, **Kickoff com o cliente** |
| 22/09/2026 | M1 concluído |
| 29/09/2026 | M2 concluído + **Checkpoint 1** |
| 06/10/2026 | M3 concluído |
| 13/10/2026 | M4 e M5 concluídos + **Checkpoint 2** ⭐ |
| 20/10/2026 | M6 (SM-2) concluído — marco crítico |
| 27/10/2026 | M7 concluído + 1ª execução E2E + **Checkpoint 3** |
| 03/11/2026 | Não-funcionais concluídos + regressão geral |
| **06/11/2026** | **Code freeze — todos os módulos prontos + UAT Final e Termo de Aceite assinado (Go/No-Go)** ⭐ |
| 17/11/2026 | Ambiente de demo validado, ensaio de apresentação concluído |
| **18/11/2026** | **Apresentação do TCC** |

---*
