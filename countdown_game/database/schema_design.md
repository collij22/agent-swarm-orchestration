# Countdown Game Database Schema Design

## Overview
This document outlines the database architecture for the Countdown Windows Game, supporting both local SQLite (client) and PostgreSQL (server) implementations.

## Entity Relationship Diagram

```
Users (1) ----< UserSessions (M)
  |
  +----< GameSessions (M) >----+ Players (M)
  |                            |
  +----< GameStatistics (1)    +----< PlayerGameHistory (M)
  |
  +----< EloRatings (1)

GameSessions (1) ----< Rounds (M) ----< RoundResults (M)
  |
  +----< GameInvites (M)

Dictionary (M) >----+ WordValidations (M)
  |
  +----< ConundrumWords (M)

LeaderboardEntries (M) >---- Users (1)
```

## Core Tables

### 1. Users Table
Primary user account information for multiplayer functionality.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    elo_rating INTEGER DEFAULT 1500,
    games_played INTEGER DEFAULT 0,
    games_won INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    best_streak INTEGER DEFAULT 0,
    total_score BIGINT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2. Game Sessions Table
Core game session data supporting all game modes.

```sql
CREATE TABLE game_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mode VARCHAR(20) NOT NULL CHECK (mode IN ('SinglePlayer', 'Multiplayer', 'Practice')),
    state VARCHAR(20) NOT NULL CHECK (state IN ('WaitingForPlayers', 'InProgress', 'RoundInProgress', 'RoundComplete', 'GameComplete', 'Abandoned')),
    current_round_index INTEGER DEFAULT 0,
    current_player_id UUID,
    invite_code VARCHAR(8) UNIQUE,
    is_rated BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    FOREIGN KEY (current_player_id) REFERENCES users(id) ON DELETE SET NULL
);
```

### 3. Players Table
Player participation in specific game sessions (supports both human and AI players).

```sql
CREATE TABLE players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_session_id UUID NOT NULL,
    user_id UUID, -- NULL for AI players
    player_name VARCHAR(100) NOT NULL,
    score INTEGER DEFAULT 0,
    starting_elo INTEGER DEFAULT 1500,
    elo_change INTEGER DEFAULT 0,
    is_ai BOOLEAN DEFAULT false,
    ai_difficulty VARCHAR(10) CHECK (ai_difficulty IN ('Easy', 'Medium', 'Hard')),
    player_order INTEGER NOT NULL,
    is_connected BOOLEAN DEFAULT true,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    FOREIGN KEY (game_session_id) REFERENCES game_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE(game_session_id, player_order)
);
```

### 4. Rounds Table
Individual round data within game sessions.

```sql
CREATE TABLE rounds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_session_id UUID NOT NULL,
    round_number INTEGER NOT NULL,
    round_type VARCHAR(10) NOT NULL CHECK (round_type IN ('Letters', 'Numbers', 'Conundrum')),
    time_limit INTEGER DEFAULT 30,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Letters round data
    selected_letters CHAR(9),
    
    -- Numbers round data
    selected_numbers INTEGER[6],
    target INTEGER,
    
    -- Conundrum round data
    conundrum_word VARCHAR(9),
    scrambled_word VARCHAR(9),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    FOREIGN KEY (game_session_id) REFERENCES game_sessions(id) ON DELETE CASCADE,
    UNIQUE(game_session_id, round_number)
);
```

### 5. Round Results Table
Player responses and scoring for each round.

```sql
CREATE TABLE round_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    round_id UUID NOT NULL,
    player_id UUID NOT NULL,
    answer VARCHAR(255),
    score INTEGER DEFAULT 0,
    submitted_at TIMESTAMP WITH TIME ZONE,
    is_valid BOOLEAN DEFAULT false,
    validation_message TEXT,
    
    -- Numbers round specific
    expression VARCHAR(500),
    calculated_result INTEGER,
    
    -- Conundrum specific
    buzzed_in BOOLEAN DEFAULT false,
    buzz_time TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    FOREIGN KEY (round_id) REFERENCES rounds(id) ON DELETE CASCADE,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    UNIQUE(round_id, player_id)
);
```

### 6. Dictionary Table
Word validation and game content.

```sql
CREATE TABLE dictionary (
    id SERIAL PRIMARY KEY,
    word VARCHAR(15) NOT NULL,
    length INTEGER NOT NULL,
    frequency_score INTEGER DEFAULT 0,
    is_common BOOLEAN DEFAULT false,
    spelling_variant VARCHAR(5) DEFAULT 'UK' CHECK (spelling_variant IN ('UK', 'US', 'BOTH')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(word, spelling_variant)
);
```

### 7. Conundrum Words Table
Pre-generated conundrum puzzles.

```sql
CREATE TABLE conundrum_words (
    id SERIAL PRIMARY KEY,
    word VARCHAR(9) NOT NULL,
    scrambled VARCHAR(9) NOT NULL,
    difficulty INTEGER DEFAULT 1 CHECK (difficulty BETWEEN 1 AND 5),
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(word)
);
```

### 8. Game Invites Table
Multiplayer game invitation management.

```sql
CREATE TABLE game_invites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_session_id UUID NOT NULL,
    invite_code VARCHAR(8) UNIQUE NOT NULL,
    created_by UUID NOT NULL,
    max_players INTEGER DEFAULT 2,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    FOREIGN KEY (game_session_id) REFERENCES game_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);
```

### 9. Leaderboard Entries Table
Cached leaderboard data for performance.

```sql
CREATE TABLE leaderboard_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    leaderboard_type VARCHAR(20) NOT NULL CHECK (leaderboard_type IN ('Global', 'Weekly', 'Monthly')),
    rank INTEGER NOT NULL,
    elo_rating INTEGER NOT NULL,
    games_played INTEGER NOT NULL,
    win_rate DECIMAL(5,4) NOT NULL,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(leaderboard_type, user_id)
);
```

### 10. User Sessions Table
Active session management for real-time features.

```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    connection_id VARCHAR(255) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

## Indexes Strategy

### Performance-Critical Indexes

```sql
-- User lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_elo_rating ON users(elo_rating DESC);
CREATE INDEX idx_users_last_activity ON users(last_activity DESC);

-- Game session queries
CREATE INDEX idx_game_sessions_state ON game_sessions(state);
CREATE INDEX idx_game_sessions_mode ON game_sessions(mode);
CREATE INDEX idx_game_sessions_invite_code ON game_sessions(invite_code);
CREATE INDEX idx_game_sessions_created_at ON game_sessions(created_at DESC);

-- Player lookups
CREATE INDEX idx_players_game_session_id ON players(game_session_id);
CREATE INDEX idx_players_user_id ON players(user_id);
CREATE INDEX idx_players_is_connected ON players(is_connected);

-- Round queries
CREATE INDEX idx_rounds_game_session_id ON rounds(game_session_id);
CREATE INDEX idx_rounds_type ON rounds(round_type);

-- Round results
CREATE INDEX idx_round_results_round_id ON round_results(round_id);
CREATE INDEX idx_round_results_player_id ON round_results(player_id);

-- Dictionary lookups (critical for performance)
CREATE INDEX idx_dictionary_word ON dictionary(word);
CREATE INDEX idx_dictionary_length ON dictionary(length);
CREATE INDEX idx_dictionary_frequency ON dictionary(frequency_score DESC);

-- Leaderboard performance
CREATE INDEX idx_leaderboard_type_rank ON leaderboard_entries(leaderboard_type, rank);
CREATE INDEX idx_leaderboard_user_type ON leaderboard_entries(user_id, leaderboard_type);

-- Session management
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_connection_id ON user_sessions(connection_id);
CREATE INDEX idx_user_sessions_active ON user_sessions(is_active) WHERE is_active = true;
```

### Composite Indexes for Complex Queries

```sql
-- Game history and statistics
CREATE INDEX idx_players_user_completed ON players(user_id, created_at DESC) 
WHERE user_id IS NOT NULL;

-- Active games lookup
CREATE INDEX idx_game_sessions_active ON game_sessions(state, created_at DESC) 
WHERE state IN ('WaitingForPlayers', 'InProgress', 'RoundInProgress');

-- Dictionary word validation
CREATE INDEX idx_dictionary_word_variant ON dictionary(word, spelling_variant);

-- Invite code management
CREATE INDEX idx_game_invites_active ON game_invites(invite_code, expires_at) 
WHERE is_active = true;
```

## Data Integrity Constraints

### Check Constraints
```sql
-- ELO rating bounds
ALTER TABLE users ADD CONSTRAINT chk_elo_rating 
CHECK (elo_rating BETWEEN 0 AND 4000);

-- Score bounds
ALTER TABLE players ADD CONSTRAINT chk_player_score 
CHECK (score >= 0);

-- Round number bounds
ALTER TABLE rounds ADD CONSTRAINT chk_round_number 
CHECK (round_number BETWEEN 1 AND 15);

-- Time limit bounds
ALTER TABLE rounds ADD CONSTRAINT chk_time_limit 
CHECK (time_limit BETWEEN 5 AND 300);
```

### Triggers for Data Consistency

```sql
-- Update user statistics trigger
CREATE OR REPLACE FUNCTION update_user_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Update user statistics when game completes
    IF NEW.state = 'GameComplete' AND OLD.state != 'GameComplete' THEN
        UPDATE users 
        SET games_played = games_played + 1,
            updated_at = NOW()
        FROM players p 
        WHERE users.id = p.user_id 
        AND p.game_session_id = NEW.id 
        AND p.user_id IS NOT NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_stats
    AFTER UPDATE ON game_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_user_stats();

-- Auto-update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_game_sessions_updated_at
    BEFORE UPDATE ON game_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

## Performance Considerations

### Query Optimization Strategies

1. **Dictionary Lookups**: Use trie-based indexing for prefix searches
2. **Leaderboard Caching**: Materialized views for complex ranking queries
3. **Session Management**: TTL-based cleanup for expired sessions
4. **Game History**: Partitioning by date for large datasets

### Scaling Recommendations

1. **Read Replicas**: For leaderboard and dictionary queries
2. **Connection Pooling**: PgBouncer for connection management
3. **Caching Layer**: Redis for session data and frequent lookups
4. **Archival Strategy**: Move completed games older than 1 year to archive tables

## Security Measures

### Data Protection
```sql
-- Row Level Security for user data
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_access_policy ON users
    FOR ALL TO application_role
    USING (id = current_setting('app.current_user_id')::UUID);

-- Audit trail for sensitive operations
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(50) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    user_id UUID,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Input Validation
- All user inputs sanitized at application layer
- Dictionary words validated against known character sets
- Expression parsing with bounds checking for numbers rounds

## Backup and Recovery

### Backup Strategy
1. **Continuous WAL archiving** for point-in-time recovery
2. **Daily full backups** with 30-day retention
3. **Weekly backup verification** with restore testing
4. **Cross-region backup replication** for disaster recovery

### Recovery Procedures
1. **Game state recovery**: Automatic reconnection handling
2. **Data corruption detection**: Checksum validation
3. **Rollback procedures**: Safe migration rollback scripts

This schema design supports all game requirements while maintaining performance, scalability, and data integrity for the Countdown Windows Game.