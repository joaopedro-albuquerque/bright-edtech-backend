-- ============================================================================
-- BRIGHT EDTECH: Script de Migração
-- Adiciona tracking de tokens e índices para performance
-- Data: 2026-09-09
-- ============================================================================

-- Passo 1: Adicionar campos de tracking de tokens em flashcards
ALTER TABLE flashcards
ADD COLUMN tokens_utilizados INT DEFAULT 0,
ADD COLUMN modelo_ia VARCHAR(100);

COMMENT ON COLUMN flashcards.tokens_utilizados IS 'Quantidade de tokens Bedrock utilizados na geração';
COMMENT ON COLUMN flashcards.modelo_ia IS 'Modelo IA utilizado (ex: claude-3-5-haiku)';

-- Passo 2: Adicionar campos de tracking de tokens em quizzes
ALTER TABLE quizzes
ADD COLUMN tokens_utilizados INT DEFAULT 0,
ADD COLUMN modelo_ia VARCHAR(100);

COMMENT ON COLUMN quizzes.tokens_utilizados IS 'Quantidade de tokens Bedrock utilizados na geração';
COMMENT ON COLUMN quizzes.modelo_ia IS 'Modelo IA utilizado (ex: claude-3-5-haiku)';

-- Passo 3: Criar índices para performance de daily-mix
-- (Se já existirem, PostgreSQL ignora com IF NOT EXISTS)
CREATE INDEX IF NOT EXISTS idx_cartoes_proxima_revisao
ON cartoes(proxima_revisao);

CREATE INDEX IF NOT EXISTS idx_cartoes_usuario_proxima
ON cartoes(usuario_id, proxima_revisao);

CREATE INDEX IF NOT EXISTS idx_questoes_proxima_revisao
ON questoes(proxima_revisao);

CREATE INDEX IF NOT EXISTS idx_questoes_usuario_proxima
ON questoes(usuario_id, proxima_revisao);

-- Passo 4: Verificar migração
SELECT
    t.tablename,
    (SELECT count(*) FROM information_schema.columns
     WHERE table_name = t.tablename AND column_name = 'tokens_utilizados') as tem_tokens
FROM pg_tables t
WHERE t.tablename IN ('flashcards', 'quizzes');

-- ============================================================================
-- Status: ✅ Migração Completa
-- Próximo passo: Atualizar backend para preencher campos tokens_utilizados
-- ============================================================================
