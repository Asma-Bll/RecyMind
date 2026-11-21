
CREATE TABLE IF NOT EXISTS utilisateurs (
    id UUID PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    mot_de_passe_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'operator'
        CHECK (role IN ('operator', 'admin', 'simulateur')),
    date_creation TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tris (
    id UUID PRIMARY KEY,
    date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    image_url TEXT NOT NULL,
    type VARCHAR(30) NOT NULL
        CHECK (type IN (
            'plastique',
            'papier_carton',
            'verre',
            'metal',
            'textile',
            'autre'
        )),
    confiance DOUBLE PRECISION NOT NULL
        CHECK (confiance >= 0 AND confiance <= 1),
    bac VARCHAR(20),
    statut VARCHAR(30) NOT NULL
        CHECK (statut IN ('trie', 'controle_manuel')),
    CHECK (
        (statut = 'controle_manuel' AND bac IS NULL)
        OR
        (statut = 'trie' AND bac IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS corrections (
    id UUID PRIMARY KEY,
    tri_id UUID NOT NULL UNIQUE
        REFERENCES tris(id) ON DELETE CASCADE,
    utilisateur_id UUID NOT NULL
        REFERENCES utilisateurs(id),
    type_corrige VARCHAR(30) NOT NULL
        CHECK (type_corrige IN (
            'plastique',
            'papier_carton',
            'verre',
            'metal',
            'textile',
            'autre'
        )),
    date_correction TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tris_date
    ON tris(date DESC);

CREATE INDEX IF NOT EXISTS idx_tris_type
    ON tris(type);

CREATE INDEX IF NOT EXISTS idx_tris_statut
    ON tris(statut);
