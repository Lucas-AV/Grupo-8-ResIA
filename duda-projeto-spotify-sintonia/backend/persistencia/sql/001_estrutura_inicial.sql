-- Estrutura conceitual migrada do D1 para SQLite.
-- TODO(Fase 4): versionar migrações e conectar repositórios Python.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuarios (
    id_pseudonimo TEXT PRIMARY KEY,
    criado_em TEXT NOT NULL,
    ultimo_acesso_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessoes (
    token_hash TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL REFERENCES usuarios(id_pseudonimo) ON DELETE CASCADE,
    criado_em TEXT NOT NULL,
    expira_em TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessoes_expira_em ON sessoes(expira_em);

CREATE TABLE IF NOT EXISTS uso_ia (
    usuario_id TEXT NOT NULL REFERENCES usuarios(id_pseudonimo) ON DELETE CASCADE,
    dia TEXT NOT NULL,
    quantidade INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (usuario_id, dia)
);

CREATE TABLE IF NOT EXISTS casos_revisao (
    id TEXT PRIMARY KEY,
    usuario_id TEXT REFERENCES usuarios(id_pseudonimo) ON DELETE SET NULL,
    mensagem_usuario TEXT NOT NULL,
    proposta_json TEXT NOT NULL,
    confianca REAL NOT NULL CHECK (confianca >= 0 AND confianca <= 1),
    motivo TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'aberto',
    nota_revisor TEXT,
    decisao_revisor_json TEXT,
    criado_em TEXT NOT NULL,
    resolvido_em TEXT,
    expira_em TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_casos_status_criado ON casos_revisao(status, criado_em);
CREATE INDEX IF NOT EXISTS idx_casos_expira_em ON casos_revisao(expira_em);

-- TODO(Fase 3): adicionar perfil resumido, recomendações exibidas e feedback
-- depois que os contratos forem validados; não copiar o schema coletivo antigo.

