# Modelo de Dados e Schema PostgreSQL

> **Fonte de verdade**: [`/schema.sql`](../schema.sql) (raiz do projeto). Este documento é uma
> transcrição comentada desse arquivo — em caso de divergência, `schema.sql` prevalece.
>
> **Banco real (produção):** `prod-brightedtech-postgres-private.cmjuyiy888yf.us-east-1.rds.amazonaws.com`,
> database `brightedtechdb`. Esse schema foi recriado do zero em **2026-09-11** a partir do
> `schema.sql` atual — antes disso, o banco tinha uma versão antiga/divergente (sem `usuario_id`
> em `cartoes`/`questoes`, sem a tabela `resumos`) que quebrava vários endpoints. Hoje o banco
> real e o `schema.sql` do repositório estão sincronizados.

## Princípio: Hybrid DB + S3

| Tipo de Dado | Localização | Motivo |
|--|--|--|
| Conteúdo de resumos (markdown completo) | S3 | Grande volume, acesso via URL pré-assinada |
| Perguntas/respostas de flashcards | S3 (JSON) | Evita inflação do banco |
| Enunciados e alternativas de quizzes | S3 (JSON) | Texto longo, reutilizável |
| Referências de arquivos (`s3_chave`) | PostgreSQL | Rápido para buscas e joins |
| Metadados do usuário | PostgreSQL | Sessão, preferências, login |
| Árvore de pastas e documentos | PostgreSQL | Queries hierárquicas eficientes |
| Estado do SM-2 (fator de facilidade, próxima revisão) | PostgreSQL | Crítico, consultado a toda hora |

---

## Diagrama de Relacionamentos

```
usuarios (1) ──< pastas (self-referencing via pasta_pai_id)
usuarios (1) ──< documentos >── pastas (opcional)
usuarios (1) ──< resumos    >── documentos
usuarios (1) ──< flashcards >── documentos (opcional)
usuarios (1) ──< quizzes    >── documentos (opcional)

flashcards (1) ──< cartoes   (estado SM-2, 1 flashcard = N cartões)
quizzes    (1) ──< questoes  (estado SM-2, 1 quiz = N questões)
```

Todas as tabelas de conteúdo (`documentos`, `resumos`, `flashcards`, `quizzes`, `cartoes`,
`questoes`) também têm uma FK direta para `usuarios` (mesmo quando já dá pra chegar lá via
join) — é **denormalização proposital**, pra permitir filtrar "tudo desse usuário" (ex: daily
mix, dashboard) sem precisar de joins extras em queries que rodam a cada request.

---

## Schema PostgreSQL Completo

### Extensão necessária

```sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```
Usada por `gen_random_uuid()` nas PKs.

---

### 1. Tabela `usuarios`

```sql
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    nome VARCHAR(255),
    cognito_id VARCHAR(255) UNIQUE,
    verificada BOOLEAN NOT NULL DEFAULT false,
    estilo_preferido VARCHAR(50),
    formato_preferido VARCHAR(50),
    objetivos_estudo TEXT,
    criado_em TIMESTAMP NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT now()
);
```

**Notas:**
- `cognito_id`: claim `sub` do JWT do Cognito — usado por `GET /profile` (ver [api-reference.md](api-reference.md#12-buscar-usuário-pelo-token-cognito--get-profile)).
- `verificada`: soft-gate, hoje não é imposta em nenhuma rota (usuário pode usar mesmo sem confirmar email).
- `estilo_preferido` (`direta`/`detalhada`/`brincalhona`) e `formato_preferido` (`resumo_executivo`/`cornell`/`fichamento_academico`): strings livres na tabela, mas validadas como enum fechado no endpoint de onboarding (`OnboardingRequest`).

---

### 2. Tabela `pastas`

```sql
CREATE TABLE pastas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    pasta_pai_id UUID REFERENCES pastas(id) ON DELETE CASCADE,
    nome VARCHAR(255) NOT NULL,
    criada_em TIMESTAMP NOT NULL DEFAULT now()
);
```

**Notas:**
- `pasta_pai_id IS NULL` → pasta raiz. Auto-relacionamento permite qualquer profundidade de aninhamento.
- `ON DELETE CASCADE` em `pasta_pai_id`: deletar uma pasta apaga toda a subárvore.

---

### 3. Tabela `documentos`

```sql
CREATE TABLE documentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    pasta_id UUID REFERENCES pastas(id) ON DELETE SET NULL,
    nome VARCHAR(255) NOT NULL,
    chave_s3 TEXT NOT NULL,
    nivel_conhecimento VARCHAR(20) NOT NULL DEFAULT 'iniciante',
    status VARCHAR(20) NOT NULL DEFAULT 'pendente'
        CHECK (status IN ('pendente', 'processando', 'pronto', 'erro', 'concluido')),
    resumo TEXT, -- LEGADO: mantido para não quebrar dados antigos; novo fluxo usa a tabela `resumos`
    criado_em TIMESTAMP NOT NULL DEFAULT now()
);
```

**Notas:**
- `chave_s3`: caminho do PDF original em S3 (`uploads/user-{id}/{document-id}.pdf`).
- `status`: `pendente` → `processando` → `pronto` (ou `erro`); `concluido` existe no CHECK mas não é usado ativamente pelo código hoje.
- `resumo` (coluna legada, TEXT solto na própria tabela): **não confundir** com a tabela `resumos` abaixo, que é o fluxo atual (N resumos por documento, conteúdo em S3).

---

### 4. Enum `modelo_resumo_enum`

```sql
CREATE TYPE modelo_resumo_enum AS ENUM ('resumo_executivo', 'cornell', 'fichamento_academico');
```

---

### 5. Tabela `resumos`

```sql
CREATE TABLE resumos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id UUID NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    titulo VARCHAR(255) NOT NULL,
    formato modelo_resumo_enum NOT NULL,
    nivel_conhecimento SMALLINT NOT NULL CHECK (nivel_conhecimento BETWEEN 0 AND 10),
    tom VARCHAR(50) NOT NULL,
    s3_chave VARCHAR(512) NOT NULL,
    tokens_utilizados INT DEFAULT 0,
    modelo_ia VARCHAR(100),
    criado_em TIMESTAMP NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT now()
);
```

**Notas:**
- Um documento pode ter **N resumos** (formatos/tons diferentes gerados a partir do mesmo PDF) — por isso `resumos` é tabela própria, não coluna de `documentos`.
- `nivel_conhecimento` e `tom` são capturados **por request** (`ResumoCreateRequest`), não herdados do perfil do usuário.
- `s3_chave` aponta pro `.md` gerado; conteúdo completo nunca fica no Postgres.
- `tokens_utilizados`/`modelo_ia`: tracking de custo do Bedrock.

---

### 6. Tabela `flashcards`

```sql
CREATE TABLE flashcards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    documento_id UUID REFERENCES documentos(id) ON DELETE SET NULL,
    titulo VARCHAR(255) NOT NULL,
    s3_chave TEXT NOT NULL,
    tokens_utilizados INT DEFAULT 0,
    modelo_ia VARCHAR(100),
    criado_em TIMESTAMP NOT NULL DEFAULT now()
);
```

`s3_chave` aponta pro JSON com a lista de pares pergunta/resposta gerados numa mesma chamada
(`POST /documentos/{id}/flashcards`). Cada item desse JSON vira uma linha em `cartoes`.

---

### 7. Tabela `cartoes` (estado SM-2 dos flashcards)

```sql
CREATE TABLE cartoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flashcard_id UUID NOT NULL REFERENCES flashcards(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    item_ref VARCHAR(100) NOT NULL,
    fator_facilidade FLOAT NOT NULL DEFAULT 2.5,
    intervalo_atual INT NOT NULL DEFAULT 0,
    repeticoes INT NOT NULL DEFAULT 0,
    proxima_revisao TIMESTAMP NOT NULL DEFAULT now()
);
```

**Notas:**
- `item_ref`: identifica qual entrada dentro do JSON em S3 (`flashcards.s3_chave`) esse cartão representa — é assim que `RevisaoService._buscar_e_enriquecer` casa a linha do banco com o conteúdo (pergunta/resposta) que vem do S3.
- `usuario_id`: denormalizado a partir de `flashcards.usuario_id`, pra filtrar "cartões pendentes deste usuário" direto (usado por `RevisaoRepository`).
- Estado do SM-2: ver seção abaixo.

---

### 8. Tabela `quizzes`

```sql
CREATE TABLE quizzes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    documento_id UUID REFERENCES documentos(id) ON DELETE SET NULL,
    titulo VARCHAR(255) NOT NULL,
    s3_chave TEXT NOT NULL,
    tokens_utilizados INT DEFAULT 0,
    modelo_ia VARCHAR(100),
    criado_em TIMESTAMP NOT NULL DEFAULT now()
);
```

Estrutura idêntica a `flashcards`; `s3_chave` aponta pro JSON com as questões geradas.

---

### 9. Tabela `questoes` (estado SM-2 dos quizzes)

```sql
CREATE TABLE questoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    item_ref VARCHAR(100) NOT NULL,
    fator_facilidade FLOAT NOT NULL DEFAULT 2.5,
    intervalo_atual INT NOT NULL DEFAULT 0,
    repeticoes INT NOT NULL DEFAULT 0,
    proxima_revisao TIMESTAMP NOT NULL DEFAULT now()
);
```

Espelha `cartoes` 1:1 (mesmas colunas, mesma lógica de SM-2), só troca `flashcard_id` por `quiz_id`.

---

## Índices

```sql
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_usuarios_cognito_id ON usuarios(cognito_id);

CREATE INDEX idx_pastas_usuario ON pastas(usuario_id);
CREATE INDEX idx_pastas_pai ON pastas(pasta_pai_id);

CREATE INDEX idx_documentos_usuario ON documentos(usuario_id);
CREATE INDEX idx_documentos_pasta ON documentos(pasta_id);

CREATE INDEX idx_resumos_documento ON resumos(documento_id);
CREATE INDEX idx_resumos_usuario ON resumos(usuario_id);

CREATE INDEX idx_flashcards_documento ON flashcards(documento_id);
CREATE INDEX idx_flashcards_usuario ON flashcards(usuario_id);

CREATE INDEX idx_cartoes_flashcard ON cartoes(flashcard_id);
CREATE INDEX idx_cartoes_usuario_proxima ON cartoes(usuario_id, proxima_revisao);

CREATE INDEX idx_quizzes_documento ON quizzes(documento_id);
CREATE INDEX idx_quizzes_usuario ON quizzes(usuario_id);

CREATE INDEX idx_questoes_quiz ON questoes(quiz_id);
CREATE INDEX idx_questoes_usuario_proxima ON questoes(usuario_id, proxima_revisao);
```

O índice composto `(usuario_id, proxima_revisao)` em `cartoes`/`questoes` é o que sustenta a
query do Daily Mix (`WHERE usuario_id = ? AND proxima_revisao <= now()`).

---

## Permissões (usuário de aplicação)

A aplicação **não conecta como `dbadmin`** (usuário master do RDS) — conecta como um role
dedicado, `api_brightedtech`, com privilégios restritos a CRUD:

```sql
GRANT USAGE ON SCHEMA public TO api_brightedtech;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO api_brightedtech;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO api_brightedtech;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO api_brightedtech;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO api_brightedtech;
```

⚠️ Sempre que o schema for recriado do zero (`DROP TABLE ... CASCADE` + reaplicar `schema.sql`),
essas `GRANT`s precisam ser reaplicadas — elas não sobrevivem ao drop das tabelas. As
credenciais desse usuário ficam em `DB_USER`/`DB_PASSWORD` no `.env` (nunca commitado — está no
`.gitignore`).

---

## SM-2 (Spaced Repetition) — como o estado é usado

Implementado em [`app/services/SpacedRepetitionService.py`](../app/services/SpacedRepetitionService.py),
consumido por [`app/services/RevisaoService.py`](../app/services/RevisaoService.py).

- `fator_facilidade` (EF): começa em `2.5`, nunca cai abaixo de `1.3`.
- `qualidade` (1 a 5, informada pelo usuário via `PUT /revisoes/cartoes/{id}/avaliar` ou
  `/revisoes/questoes/{id}/avaliar`):
  - `q < 3` (errou) → `repeticoes = 0`, `intervalo_atual = 1`
  - `q >= 3` (acertou):
    - `repeticoes == 0` → `intervalo_atual = 1`
    - `repeticoes == 1` → `intervalo_atual = 6`
    - `repeticoes > 1` → `intervalo_atual = ceil(intervalo_anterior * EF_atual)`
    - `repeticoes += 1`
  - `EF_novo = max(1.3, EF_atual + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))`
- `proxima_revisao = now() + intervalo_atual dias`

Regras completas e exemplos de request/response em
[api-reference.md § Revisões](api-reference.md#7-revisões--daily-mix-sm-2).

---

## Fluxo de Dados Exemplificado

### Upload de PDF → gerar resumo

```
1. POST /documentos/upload (multipart)
   └─> INSERT documentos (status='pendente', chave_s3=...)

2. POST /documentos/{documento_id}/resumos
   └─> Bedrock gera o resumo com base no PDF + parâmetros do request
   └─> S3: salva markdown em artifacts/user-{id}/doc-{id}/resumo-{id}.md
   └─> INSERT resumos (s3_chave=..., tokens_utilizados=..., modelo_ia=...)
```

### Daily Mix → avaliar um cartão

```
1. GET /revisoes/hoje
   └─> SELECT cartoes/questoes WHERE usuario_id = ? AND proxima_revisao <= now()
   └─> Para cada item, busca o JSON em S3 (flashcards.s3_chave) e casa pelo item_ref

2. PUT /revisoes/cartoes/{cartao_id}/avaliar { "qualidade": 4 }
   └─> Aplica SM-2 (SpacedRepetitionService)
   └─> UPDATE cartoes SET fator_facilidade, intervalo_atual, repeticoes, proxima_revisao
```

---

## Notas de Consistência

1. **Sem duplicação de conteúdo**: texto de resumos/flashcards/quizzes nunca é duplicado entre S3 e PostgreSQL — o banco só guarda a referência (`s3_chave`) e o estado de revisão.
2. **Referências imutáveis**: uma vez escrito em S3, o arquivo é read-only (nova geração = novo arquivo, nova linha no banco).
3. **`ON DELETE CASCADE`** em quase todas as FKs: deletar um usuário apaga toda a árvore de dados dele (pastas, documentos, resumos, flashcards/cartões, quizzes/questões). Não há soft-delete hoje.
4. **Recriar o schema do zero**: use exatamente `schema.sql` (`psql ... -f schema.sql`, ou via `psycopg2` executando o arquivo inteiro) e não esqueça de reaplicar as `GRANT`s da seção acima — sem elas a API conecta mas recebe `permission denied` em qualquer query.

---

**Última atualização:** 2026-09-11 — sincronizado com o schema real de produção após recriação completa do banco.
