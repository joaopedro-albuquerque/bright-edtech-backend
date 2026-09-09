# Modelo de Dados e Schema PostgreSQL

> **Fonte de verdade do schema real**: [`/schema.sql`](../schema.sql) (raiz do projeto).
> Este documento descreve a arquitetura conceitual; pequenas diferenças de nomes de
> coluna existem no schema real (ex.: `documentos.chave_s3` em vez de `s3_chave`,
> `resumos.formato/nivel_conhecimento/tom` capturados por request em vez de herdados
> do perfil, `usuarios.nome`/`cognito_id` para integração com AWS Cognito). Em caso de
> divergência, `schema.sql` prevalece.

## Princípio: Hybrid DB + S3

| Tipo de Dado | Localização | Motivo |
|--|--|--|
| Conteúdo de resumos (texto completo) | S3 | Grande volume, acesso via URL |
| Enunciados de quizzes | S3 | Texto longo, reutilizável |
| Perguntas e respostas de flashcards | S3 | Evita inflação do DB |
| Referências de arquivos (s3_chave, URL) | PostgreSQL | Rápido para buscas e joins |
| Metadados do usuário | PostgreSQL | Sessão, preferências, login |
| Árvore de pastas e documentos | PostgreSQL | Queries hierárquicas eficientes |
| Estado do SM-2 (fator de facilidade, próxima_revisao) | PostgreSQL | Crítico para algoritmo de revisão |

---

## Schema PostgreSQL Completo

### 1. Tabela `usuarios`
Armazena dados de cadastro e preferências globais do usuário.

```sql
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    verificada BOOLEAN DEFAULT false,
    estilo_preferido VARCHAR(50),              -- ex: "linguagem mais direta, brincalhona, algo assim)
    formato_preferido VARCHAR(50),             -- ex: "cornell", "resumo_executivo"
    objetivos_estudo TEXT,                     -- texto livre (ex: "passar em concurso")
    criado_em TIMESTAMP NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT now()
);
```

**Notas:**
- `verificada`: Soft-gate (usuário pode usar sem email verificado inicialmente)
- `estilo_preferido` e `formato_preferido`: Valores padrão herdados por documentos/pastas

---

### 2. Tabela `pastas`
Hierarquia de pastas para organizar documentos.

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
- `pasta_pai_id` NULL = pasta raiz
- Suporta infinitos níveis de aninhamento
- Herança de configuração: Documento > Pasta > Perfil Global

---

### 3. Tabela `documentos`
Armazena PDFs uploadados e seu status de processamento.

```sql
CREATE TABLE documentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    pasta_id UUID REFERENCES pastas(id) ON DELETE SET NULL,
    nome VARCHAR(255) NOT NULL,
    s3_chave TEXT NOT NULL UNIQUE,            -- ex: "uploads/user-123/document-456.pdf"
    status VARCHAR(20) NOT NULL DEFAULT 'pendente' 
        CHECK (status IN ('pendente', 'processando', 'pronto', 'erro')),
    criado_em TIMESTAMP NOT NULL DEFAULT now()
);
```

**Estados:**
- `pendente`: Aguardando processamento
- `processando`: Extração de texto em andamento
- `pronto`: Pronto para geração de artefatos
- `erro`: Falha no processamento

---

### 4. Enum `modelo_resumo_enum`
Define os tipos de resumo suportados.

```sql
CREATE TYPE modelo_resumo_enum AS ENUM (
    'resumo_executivo', 
    'cornell', 
    'fichamento_academico'
);
```

---

### 5. Tabela `resumos`
Metadados sobre resumos gerados.

```sql
CREATE TABLE resumos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id UUID NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    titulo VARCHAR(255) NOT NULL,
    modelo modelo_resumo_enum NOT NULL,
    s3_chave VARCHAR(512) NOT NULL,           -- ex: "artifacts/user-123/doc-456/resumo-001.md"
    tokens_utilizados INT DEFAULT 0,          -- para tracking de custos
    modelo_ia VARCHAR(100),                   -- ex: "claude-3-5-sonnet"
    criado_em TIMESTAMP NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT now()
);
```

**Notas:**
- `s3_chave`: Aponta para o arquivo `.md` em S3
- `tokens_utilizados`: Métrica de custo (para análise futura)
- Conteúdo completo do resumo está em S3, não aqui

---

### 6. Tabela `flashcards`
Coleção de cartões de revisão associados a um documento.

```sql
CREATE TABLE flashcards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    documento_id UUID REFERENCES documentos(id) ON DELETE SET NULL,
    titulo VARCHAR(255) NOT NULL,
    s3_chave TEXT NOT NULL,                   -- ex: "artifacts/user-123/doc-456/flashcard-001.json"
    tokens_utilizados INT DEFAULT 0,          -- para tracking de custos (Bedrock)
    modelo_ia VARCHAR(100),                   -- ex: "claude-3-5-haiku"
    criado_em TIMESTAMP NOT NULL DEFAULT now()
);
```

**Notas:**
- S3 armazena JSON com estrutura de pares pergunta-resposta
- Cada flashcard pode ter múltiplos cartões (1:N via `cartoes`)
- `tokens_utilizados` e `modelo_ia` rastreiam custo de geração IA

---

### 7. Tabela `cartoes` (Spaced Repetition State)
**Armazena o estado do algoritmo SM-2 para cada item de revisão.**

```sql
CREATE TABLE cartoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flashcard_id UUID NOT NULL REFERENCES flashcards(id) ON DELETE CASCADE,
    item_ref VARCHAR(100) NOT NULL,           -- ex: "card_001", "card_002" (ID dentro do JSON)
    fator_facilidade FLOAT NOT NULL DEFAULT 2.5,   -- EF do SM-2 (começa em 2.5)
    intervalo_atual INT NOT NULL DEFAULT 0,        -- dias desde última revisão
    repeticoes INT NOT NULL DEFAULT 0,             -- quantidade de vezes revisado
    proxima_revisao TIMESTAMP NOT NULL DEFAULT now()
);
```

**Algoritmo SM-2:**
- `fator_facilidade` varia de 1.3 a 5.0
- Ajustado pela resposta do usuário (1-5)
- `proxima_revisao` = hoje + (intervalo_atual * fator_facilidade)

---

### 8. Tabela `quizzes` (Similar a `flashcards`)
```sql
CREATE TABLE quizzes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    documento_id UUID REFERENCES documentos(id) ON DELETE SET NULL,
    titulo VARCHAR(255) NOT NULL,
    s3_chave TEXT NOT NULL,                   -- ex: "artifacts/user-123/doc-456/quiz-001.json"
    tokens_utilizados INT DEFAULT 0,          -- para tracking de custos (Bedrock)
    modelo_ia VARCHAR(100),                   -- ex: "claude-3-5-haiku"
    criado_em TIMESTAMP NOT NULL DEFAULT now()
);
```

---

### 9. Tabela `questoes` (Similar a `cartoes`)
```sql
CREATE TABLE questoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    item_ref VARCHAR(100) NOT NULL,           -- ex: "q_001"
    fator_facilidade FLOAT NOT NULL DEFAULT 2.5,
    intervalo_atual INT NOT NULL DEFAULT 0,
    repeticoes INT NOT NULL DEFAULT 0,
    proxima_revisao TIMESTAMP NOT NULL DEFAULT now()
);
```

---

## Fluxo de Dados Exemplificado

### Cenário: Usuário faz upload de PDF e gera resumo

```
1. POST /api/documents (upload)
   └─> INSERT documentos (status='pendente')
   └─> S3: Salva PDF em /uploads/user-123/doc-456.pdf

2. Async: Processamento de PDF
   └─> UPDATE documentos SET status='pronto'

3. POST /api/documents/{doc_id}/resumos
   └─> Bedrock: Gera resumo com System Prompt
   └─> S3: Salva resumo em /artifacts/user-123/doc-456/resumo.md
   └─> INSERT resumos (s3_chave=..., tokens_utilizados=1234)

4. GET /api/documents/{doc_id}/resumos/{resumo_id}
   └─> SELECT resumos WHERE id = ...
   └─> Retorna s3_chave
   └─> Frontend faz GET em S3 para conteúdo completo
   └─> TipTap editor renderiza Markdown
```

### Cenário: Daily Mix - Revisão de Flashcards

```
1. GET /api/daily-mix
   └─> SELECT cartoes WHERE proxima_revisao <= TODAY

2. Frontend exibe cada cartão
   └─> GET S3 para conteúdo (pergunta/resposta)
   └─> Usuário responde (classifica 1-5)

3. POST /api/cartoes/{cartao_id}/responder
   ├─> Aplica SM-2
   ├─> novo_fator = max(1.3, fator - 0.08 + 0.02*(5-grade))
   ├─> novo_intervalo = intervalo * novo_fator (se grade >= 3)
   ├─> nova_proxima = TODAY + novo_intervalo
   └─> UPDATE cartoes SET fator_facilidade, intervalo_atual, proxima_revisao

4. Frontend atualiza (próxima revisão em X dias)
```

---

## Índices Recomendados

```sql
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_documentos_usuario ON documentos(usuario_id);
CREATE INDEX idx_documentos_pasta ON documentos(pasta_id);
CREATE INDEX idx_resumos_documento ON resumos(documento_id);
CREATE INDEX idx_cartoes_proxima_revisao ON cartoes(proxima_revisao);
CREATE INDEX idx_cartoes_flashcard ON cartoes(flashcard_id);
CREATE INDEX idx_questoes_proxima_revisao ON questoes(proxima_revisao);
```

---

## Script de Migração (Atualizar Banco Existente)

Se seu banco já existe, execute este script para adicionar campos de tracking de tokens:

```sql
-- Adicionar campos em flashcards
ALTER TABLE flashcards ADD COLUMN tokens_utilizados INT DEFAULT 0;
ALTER TABLE flashcards ADD COLUMN modelo_ia VARCHAR(100);

-- Adicionar campos em quizzes
ALTER TABLE quizzes ADD COLUMN tokens_utilizados INT DEFAULT 0;
ALTER TABLE quizzes ADD COLUMN modelo_ia VARCHAR(100);

-- Índices já devem estar criados (verifique antes de criar duplicados)
CREATE INDEX idx_cartoes_proxima_revisao ON cartoes(proxima_revisao);
CREATE INDEX idx_questoes_proxima_revisao ON questoes(proxima_revisao);
```

**Aplicar:**
```bash
psql -h {DB_HOST} -U {DB_USER} -d bright_db -f migrations/add_token_tracking.sql
```

---

## Notas de Consistência

1. **Sem Duplicação:** Conteúdo de resumos **nunca** é duplicado entre S3 e PostgreSQL
2. **Referências Imutáveis:** Uma vez escrito em S3, o arquivo é read-only (nova versão = novo arquivo)
3. **Soft Deletes Opcional:** Documentos/pastas podem ser soft-delete se necessário auditoria
4. **Backup:** S3 versioning + PostgreSQL backups automáticos recomendados
