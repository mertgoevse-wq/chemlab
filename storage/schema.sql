-- Chemlab Storage Engine Schema
-- Designed for Local Secure SQLite Persistence with Cloud Sync Metadata
-- Optimized for high performance, ACID integrity, and low memory footprint (Intel Iris Xe)

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- 1. Player Profiles
CREATE TABLE IF NOT EXISTS player_profiles (
    player_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    email_hash TEXT,
    level INTEGER NOT NULL DEFAULT 1,
    experience_points INTEGER NOT NULL DEFAULT 0,
    settings_json TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER NOT NULL DEFAULT 1
);

-- 2. Unlocked Levels & Progress
CREATE TABLE IF NOT EXISTS unlocked_levels (
    player_id TEXT NOT NULL,
    level_id TEXT NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    stars INTEGER NOT NULL DEFAULT 0,
    best_time_seconds REAL NOT NULL DEFAULT 0.0,
    reaction_accuracy REAL NOT NULL DEFAULT 0.0,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    signature TEXT NOT NULL,
    PRIMARY KEY (player_id, level_id),
    FOREIGN KEY (player_id) REFERENCES player_profiles(player_id) ON DELETE CASCADE
);

-- 3. High Scores & Leaderboard Cache
CREATE TABLE IF NOT EXISTS high_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level_id TEXT NOT NULL,
    player_id TEXT NOT NULL,
    score INTEGER NOT NULL,
    reaction_accuracy REAL DEFAULT 0.0,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    signature TEXT NOT NULL,
    FOREIGN KEY (player_id) REFERENCES player_profiles(player_id) ON DELETE CASCADE
);

-- 4. Custom Reaction Recipes (Kinetics, Thermodynamics, Reagents)
CREATE TABLE IF NOT EXISTS custom_reaction_recipes (
    recipe_id TEXT PRIMARY KEY,
    player_id TEXT NOT NULL,
    name TEXT NOT NULL,
    formula TEXT,
    reactants_json TEXT NOT NULL,
    kinetics_json TEXT,
    thermodynamics_json TEXT,
    safety_notes TEXT,
    is_verified INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES player_profiles(player_id) ON DELETE CASCADE
);

-- 5. Saved Experiments & Lab State
CREATE TABLE IF NOT EXISTS saved_experiments (
    experiment_id TEXT PRIMARY KEY,
    player_id TEXT NOT NULL,
    name TEXT NOT NULL,
    apparatus_config_json TEXT NOT NULL,
    chemical_state_json TEXT NOT NULL,
    oscillation_state_json TEXT,
    simulation_timestep REAL NOT NULL DEFAULT 0.01,
    thumbnail_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES player_profiles(player_id) ON DELETE CASCADE
);

-- 6. Asset Cache Metadata (CAS Content-Addressable Storage)
CREATE TABLE IF NOT EXISTS asset_cache_metadata (
    asset_id TEXT PRIMARY KEY,
    asset_uri TEXT UNIQUE NOT NULL,
    local_path TEXT NOT NULL,
    sha256_hash TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    asset_type TEXT NOT NULL,
    mime_type TEXT,
    is_pinned INTEGER NOT NULL DEFAULT 0,
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Sync Journal (Offline Mutation Queue for Google Drive / Cloud Sync)
CREATE TABLE IF NOT EXISTS sync_journal (
    journal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'PENDING'
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_levels_player ON unlocked_levels(player_id);
CREATE INDEX IF NOT EXISTS idx_high_scores_level ON high_scores(level_id, score DESC);
CREATE INDEX IF NOT EXISTS idx_recipes_player ON custom_reaction_recipes(player_id);
CREATE INDEX IF NOT EXISTS idx_experiments_player ON saved_experiments(player_id);
CREATE INDEX IF NOT EXISTS idx_asset_cache_accessed ON asset_cache_metadata(last_accessed_at ASC);
CREATE INDEX IF NOT EXISTS idx_sync_journal_status ON sync_journal(status, created_at ASC);
