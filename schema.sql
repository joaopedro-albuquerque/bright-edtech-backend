-- ============================================================================
-- BRIGHT EDTECH: Schema Completo do Banco de Dados
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- USUÁRIOS
-- ============================================================================
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

-- ============================================================================
-- PASTAS
-- ============================================================================
CREATE TABLE pastas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    pasta_pai_id UUID REFERENCES pastas(id) ON DELETE CASCADE,
    nome VARCHAR(255) NOT NULL,
    criada_em TIMESTAMP NOT NULL DEFAULT now()
);

-- ============================================================================
-- DOCUMENTOS
-- ============================================================================
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

-- ============================================================================
-- RESUMOS (N por documento, conteúdo em S3)
-- ============================================================================
CREATE TYPE modelo_resumo_enum AS ENUM ('resumo_executivo', 'cornell', 'fichamento_academico');

CREATE TABLE resumos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id UUID NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    titulo VARCHAR(255) NOT NULL,
    formato modelo_resumo_enum NOT NULL,
    nivel_conhecimento SMALLINT NOT NULL CHECK (nivel_conhecimento BETWEEN 0 AND 10),
    tom VARCHAR(50) NOT NULL,
    s3_chave VARCHAR(512) NOT NULL,
    s3_chave_pdf VARCHAR(512), -- PDF gerado a partir do markdown; NULL = ainda não gerado (backfill preguiçoso no download)
    tokens_utilizados INT DEFAULT 0,
    modelo_ia VARCHAR(100),
    criado_em TIMESTAMP NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT now()
);

-- ============================================================================
-- FLASHCARDS + CARTÕES (Spaced Repetition)
-- ============================================================================
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

-- ============================================================================
-- QUIZZES + QUESTÕES (Spaced Repetition)
-- ============================================================================
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

-- ============================================================================
-- ÍNDICES
-- ============================================================================
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
