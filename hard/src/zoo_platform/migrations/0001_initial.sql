CREATE TABLE enclosures (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE animals (
    id INTEGER PRIMARY KEY,
    tenant TEXT NOT NULL,
    name TEXT NOT NULL,
    species TEXT NOT NULL,
    enclosure_id INTEGER NOT NULL REFERENCES enclosures (id),
    arrived_at INTEGER NOT NULL
);

CREATE TABLE facts (
    topic TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE TABLE meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id INTEGER NOT NULL REFERENCES animals (id),
    grams INTEGER NOT NULL CHECK (grams > 0),
    supplier_ref TEXT,
    created_at INTEGER NOT NULL
);

CREATE TABLE bellies (
    animal_id INTEGER PRIMARY KEY REFERENCES animals (id),
    grams INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE kittens (
    id TEXT PRIMARY KEY,
    tenant TEXT NOT NULL,
    name TEXT NOT NULL,
    adopted_by TEXT
);

CREATE TABLE pantries (
    id TEXT PRIMARY KEY,
    tenant TEXT NOT NULL,
    food_kg INTEGER NOT NULL CHECK (food_kg >= 0)
);

CREATE TABLE pens (
    id TEXT PRIMARY KEY,
    tenant TEXT NOT NULL,
    dirty INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE api_keys (
    key_id TEXT PRIMARY KEY,
    key_hash TEXT NOT NULL,
    subject TEXT NOT NULL,
    tenant TEXT NOT NULL,
    scopes TEXT NOT NULL DEFAULT ''
);
