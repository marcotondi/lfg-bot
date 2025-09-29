-- migrate:up

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    mute BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_master BOOLEAN DEFAULT 0,
    is_admin BOOLEAN DEFAULT 0
);

-- Tables table
CREATE TABLE IF NOT EXISTS tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    master_id INTEGER NOT NULL,
    type TEXT CHECK(type IN ('one_shot', 'campaign')) NOT NULL,
    game TEXT NOT NULL,
    name TEXT NOT NULL,
    max_players INTEGER NOT NULL,
    description TEXT,
    image TEXT,
    num_sessions INTEGER,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (master_id) REFERENCES users(id)
);

-- Registrations table
CREATE TABLE IF NOT EXISTS registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (table_id) REFERENCES tables(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(table_id, user_id)
);

-- Trigger for registrations updated_at
CREATE TRIGGER IF NOT EXISTS update_registrations_updated_at
AFTER UPDATE ON registrations
FOR EACH ROW
BEGIN
    UPDATE registrations SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE INDEX idx_users ON users(telegram_id);
CREATE INDEX idx_tables ON tables(master_id);
CREATE INDEX idx_registrations ON registrations(table_id);

-- migrate:down

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS tables;
DROP TABLE IF EXISTS registrations;

DROP TRIGGER IF EXISTS update_registrations_updated_at;