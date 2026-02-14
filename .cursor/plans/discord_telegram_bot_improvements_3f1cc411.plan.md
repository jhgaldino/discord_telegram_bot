---
name: Discord Telegram Bot Improvements
overview: Refactor and modernize the Discord-Telegram bot with improved command management, database organization, channel management, permission system, dev environment setup (with development-only features), and UI modernization.
todos:
  - id: db_refactor
    content: Create Database class in src/shared/database.py with proper connection management and refactor reminders.py to use it
    status: completed
  - id: permissions
    content: Create shared permission system in src/shared/permissions.py and apply to relevant commands
    status: completed
  - id: reminders_groups
    content: Upgrade reminders to support groups with multi-text matching (create reminder_groups and reminder_texts tables)
    status: completed
  - id: channel_db
    content: Create database tables for Discord and Telegram channels and update forwarder to load from database
    status: completed
  - id: channel_commands
    content: Create channels.py cog with add/remove/list commands for both Discord and Telegram channels
    status: completed
  - id: config_cleanup
    content: Remove global config object from config.py, keep only get_bot() and get_client(), update main.py to use database for channels
    status: completed
  - id: command_cleanup
    content: Identify and remove redundant commands from info.py cog
    status: completed
  - id: dev_env
    content: Configure pyproject.toml with uv, ruff, and ty type checker settings
    status: completed
  - id: dev_features
    content: Make log level INFO and cog hot-reload conditional based on development environment variable
    status: completed
  - id: ci_workflow
    content: Create .github/workflows/ci.yml with linting, type checking, and build verification
    status: completed
  - id: sqlalchemy_migration
    content: Migrate from raw SQL to SQLAlchemy ORM with support for both SQLite and PostgreSQL (using Alembic for migrations)
    status: pending
  - id: ui_modernize
    content: Convert all commands to use embeds and add interactive views (buttons) for reminder and channel management
    status: pending
  - id: migration_architecture
    content: Create organized SQLite migration architecture with migration tracking, versioning, and automatic migration execution
    status: cancelled
isProject: false
---

# Discord Telegram Bot Improvements Plan

## Overview

This plan covers 12 major improvements to modernize and refactor the Discord-Telegram bot application, including command cleanup, permission system, database refactoring, migration architecture, SQLAlchemy migration, channel management, config simplification, dev environment setup with development-only features (log level and hot-reload), CI/CD, and UI modernization.

## Current Architecture

The application consists of:

- **Discord Bot** (`src/services/discord/bot.py`) - Custom Bot class with cog loading
- **Telegram Client** (`src/services/telegram/client.py`) - TelegramClientManager for Telegram integration
- **Message Forwarder** (`src/services/telegram/forwarder.py`) - Forwards messages from Telegram to Discord
- **Cogs**: `info`, `lembretes` (reminders), `telegram` - Command groups
- **Config** (`src/config.py`) - Global config object with environment variable loading
- **Database** (`src/shared/reminders.py`) - Raw SQLite for reminders storage

## Implementation Plan

### 1. Remove Redundant Commands from `src/cogs/info.py`

**Current commands:**

- `/info` - General bot information (name, ID, servers, users, uptime, versions)
- `/serverinfo` - Server-specific information (name, ID, owner, members, channels, roles)
- `/status` - Bot operational status with Telegram connection info (owner-only)

**Action:** Analyze command overlap and remove redundant ones. `/info` and `/serverinfo` provide general information, while `/status` is operational. Keep `/status` for owner diagnostics and one general info command.**Files to modify:**

- `src/cogs/info.py` - Remove redundant command(s)

### 2. Implement Permission System

**Current state:**

- `_is_owner()` method in `Info` cog
- `is_owner()` function in `telegram.py` cog
- No centralized permission system

**Action:**

- Create a shared permission decorator/check system in `src/shared/permissions.py`
- Support bot owner checks and allowed users list
- Apply restrictions to sensitive commands (e.g., `/telegram login`, `/status`)
- Use `app_commands.checks` decorators for clean integration

**Files to create:**

- `src/shared/permissions.py` - Permission checking utilities

**Files to modify:**

- `src/cogs/info.py` - Use shared permission system
- `src/cogs/telegram.py` - Use shared permission system
- `src/cogs/reminders.py` - Add permission checks if needed

### 3. Upgrade Reminders Logic for Multi-Text Matches

**Current state:**

- Single text match per user using `INSTR(LOWER(?), LOWER(reminder))`
- Stored in `reminders` table with `(user_id, reminder)` unique constraint

**Action:**

- Refactor to support reminder groups where all texts in a group must match
- Add `reminder_groups` table: `(id, user_id, group_name)`
- Add `reminder_texts` table: `(id, group_id, text)`
- Update matching logic to check all texts in a group
- Migrate existing reminders to default groups
- Update commands to support group management

**Database schema:**

```sql
CREATE TABLE reminder_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    group_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, group_name)
);

CREATE TABLE reminder_texts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    FOREIGN KEY (group_id) REFERENCES reminder_groups(id) ON DELETE CASCADE,
    UNIQUE(group_id, text)
);
```

**Files to modify:**

- `src/shared/reminders.py` - Refactor to use new schema and group logic
- `src/cogs/reminders.py` (cog name: `lembretes`) - Update commands for group management
- Current commands: `/lembretes adicionar`, `/lembretes listar`, `/lembretes remover`

### 4. Organize Database Logic

**Current state:**

- Raw SQLite connections and queries in `src/shared/reminders.py`
- Global `connection` and `cursor` objects
- No connection pooling or proper resource management

**Action:**

- Create `src/shared/database.py` with a `Database` class
- Implement proper connection management (context managers, async support)
- Refactor reminders to use the Database class
- Create separate table management methods
- Add migration support for schema changes

**Files to create:**

- `src/shared/database.py` - Database management class

**Files to modify:**

- `src/shared/reminders.py` - Use Database class
- Update all database access to use the new class

### 4a. Organized SQLite Migration Architecture

**Current state:**

- Ad-hoc migration logic embedded in table initialization functions (e.g., `_migrate_old_reminders()` in `reminder_groups.py`)
- Migration tracking using marker tables (e.g., `_reminders_migrated` table in `reminder_groups.py`)
- SQLite's `PRAGMA user_version` exists but is currently 0 (not being used)
- No centralized migration system or versioning
- Table creation scattered across modules with `table_exists()` checks
- No way to track migration history or rollback

**Action:**

- Create a migration system in `src/database/migrations/` directory:
- `__init__.py` - Migration registry and runner
- `migration.py` - Base `Migration` class with `up()` and `down()` methods
- `runner.py` - `MigrationRunner` class to discover, track, and execute migrations
- Individual migration files: `001_initial_schema.py`, `002_reminder_groups.py`, etc.
- Use SQLite's `PRAGMA user_version` to track applied migrations (replacing marker table approach):
- Read current version with `PRAGMA user_version` (currently 0, unused)
- Each migration has a version number (matches file prefix: 001, 002, etc.)
- After successful migration, update with `PRAGMA user_version = <version>`
- Migration runner only executes migrations with version > current `user_version`
- No additional tables needed - uses SQLite's built-in version tracking
- Migration from marker tables: When converting existing migrations, check for marker tables (e.g., `_reminders_migrated`) and set appropriate `user_version` before running new migrations
- Migration file structure:
- Numbered prefix for ordering (e.g., `001_`, `002_`)
- Descriptive name (e.g., `initial_schema`, `reminder_groups`)
- Each migration implements `up()` and optionally `down()` methods
- Migrations can include both schema changes and data migrations
- Migration runner features:
- Auto-discover migrations from `src/database/migrations/` directory
- Execute migrations in order based on version number
- Read current version from `PRAGMA user_version` (defaults to 0 for new databases)
- Only execute migrations with version number > current `user_version`
- Update `PRAGMA user_version` after each successful migration
- Support for rollback (if `down()` method implemented)
- Transaction support for atomic migrations (each migration runs in a transaction)
- Refactor existing table initialization:
- Convert `_init_reminders_tables()` logic to migration files
- Convert `_migrate_old_reminders()` to a migration
- Handle transition from marker tables: Check for `_reminders_migrated` table and set `user_version` accordingly (e.g., if marker exists, set version to 2)
- Remove ad-hoc `table_exists()` checks from module-level code
- Remove marker table creation logic (replaced by `PRAGMA user_version`)
- Call migration runner on application startup
- Integration with Database class:
- Add `run_migrations()` method to `Database` class
- Or create separate `MigrationRunner` that uses `Database` instance
- Ensure migrations run before any table access

**Migration file example:**

```python
from src.database.migrations.migration import Migration

class Migration002ReminderGroups(Migration):
    """Migrate reminders to group-based structure."""

    # Version number matches file prefix (002)
    version = 2

    def up(self, db):
        # Create tables
        db.execute("""
            CREATE TABLE reminder_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                group_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, group_name)
            )
        """)
        # ... more schema changes

        # Data migration
        if db.table_exists("reminders"):
            # Migrate old data
            ...

    def down(self, db):
        # Rollback logic (optional)
        db.execute("DROP TABLE IF EXISTS reminder_texts")
        db.execute("DROP TABLE IF EXISTS reminder_groups")
```

**Migration runner logic:**

- Read current version: `PRAGMA user_version` (returns integer, default 0)
- Discover all migrations and sort by version number
- Execute migrations where `migration.version > current_user_version`
- After each successful migration: `PRAGMA user_version = migration.version`
- If migration fails, transaction rolls back and `user_version` remains unchanged

**Files to create:**

- `src/database/migrations/__init__.py` - Migration registry and public API
- `src/database/migrations/migration.py` - Base Migration class
- `src/database/migrations/runner.py` - MigrationRunner class
- `src/database/migrations/001_initial_schema.py` - Initial database schema
- `src/database/migrations/002_reminder_groups.py` - Reminder groups migration
- Additional migration files as needed

**Files to modify:**

- `src/database/database.py` - Add migration runner integration or helper method
- `src/database/reminder_groups.py` - Remove `_init_reminders_tables()` and `_migrate_old_reminders()`, replace with migration calls
- `main.py` - Call migration runner on startup (before any database access)
- Any other modules with table initialization logic - convert to migrations

**Benefits:**

- Version-controlled schema changes
- Reproducible database state across environments
- Clear migration history
- Easier rollback capabilities
- Separation of concerns (migrations separate from business logic)
- Better testing (can test migrations independently)

### 4b. SQLAlchemy Migration with Multi-Database Support

**Priority: NEXT** - This is the next major task. Alembic will handle migrations (no need for custom migration architecture).**Current state:**

- Raw SQL queries using `sqlite3` directly
- Database class with manual connection management
- SQLite-specific code (e.g., `PRAGMA` statements)
- No abstraction for different database backends
- Manual table creation and migration logic

**Action:**

- Migrate from raw SQL to SQLAlchemy ORM:
- Install SQLAlchemy and database-specific drivers (e.g., `psycopg2` or `asyncpg` for PostgreSQL)
- Create SQLAlchemy models for all tables:
- `ReminderGroup` model (replaces `reminder_groups` table)
- `ReminderText` model (replaces `reminder_texts` table)
- `DiscordChannel` model (replaces `discord_channels` table)
- `TelegramChannel` model (replaces `telegram_channels` table)
- Use SQLAlchemy's declarative base and relationships
- Replace raw SQL queries with SQLAlchemy ORM queries
- Support both SQLite and PostgreSQL:
- Use SQLAlchemy's engine abstraction with database URL
- Configure database URL via environment variable (`DATABASE_URL`)
- SQLite: `sqlite:///database.db`
- PostgreSQL: `postgresql://user:password@host:port/dbname` or `postgresql+psycopg2://...`
- Use SQLAlchemy's dialect system to handle database-specific differences
- Avoid SQLite-specific features (e.g., `PRAGMA user_version` → use Alembic versioning instead)
- Replace custom Database class:
- Use SQLAlchemy's `Session` and `Engine` for connection management
- Create session factory or use dependency injection pattern
- Keep similar API surface if possible (e.g., `get_database()` returns session/engine)
- Use Alembic for migrations:
- Replace custom migration system with Alembic
- Alembic supports both SQLite and PostgreSQL
- Generate migrations from model changes
- Use `alembic upgrade head` for migrations
- Update all database access:
- Convert `reminder_groups.py` functions to use SQLAlchemy models
- Convert `channels.py` functions to use SQLAlchemy models
- Update all queries to use SQLAlchemy ORM instead of raw SQL
- Use relationships for foreign keys (e.g., `ReminderText.group` relationship)

**SQLAlchemy model example:**

```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class ReminderGroup(Base):
    __tablename__ = "reminder_groups"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    group_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    texts = relationship("ReminderText", back_populates="group", cascade="all, delete-orphan")

    __table_args__ = (
        {"sqlite_autoincrement": True},  # SQLite-specific
    )
```

**Database URL configuration:**

- Environment variable: `DATABASE_URL`
- Default to SQLite for backward compatibility: `sqlite:///database.db`
- Support PostgreSQL: `postgresql://user:pass@host:port/dbname`
- Use SQLAlchemy's `create_engine()` with URL parsing

**Session management:**

- Create `SessionLocal` factory for session creation
- Use context managers or dependency injection for session lifecycle
- Ensure proper session cleanup (commit/rollback)

**Files to create:**

- `src/database/models.py` - SQLAlchemy model definitions
- `src/database/session.py` - Session factory and engine setup
- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Alembic environment setup
- `alembic/versions/` - Migration files (auto-generated)

**Files to modify:**

- `src/database/database.py` - Replace with SQLAlchemy session/engine management
- `src/database/reminder_groups.py` - Convert to SQLAlchemy ORM queries
- `src/database/channels.py` - Convert to SQLAlchemy ORM queries
- `requirements.txt` or `pyproject.toml` - Add SQLAlchemy and database drivers
- `main.py` - Initialize SQLAlchemy engine on startup

**Benefits:**

- Database-agnostic code (works with SQLite and PostgreSQL)
- Type-safe ORM queries
- Automatic relationship handling
- Alembic for professional migrations
- Better error handling and connection pooling
- Easier testing (can use in-memory SQLite for tests)
- Industry-standard approach

**Considerations:**

- SQLAlchemy adds some overhead compared to raw SQL
- Need to handle database-specific differences (e.g., auto-increment, datetime handling)
- Alembic replaces custom migration system
- May need to update existing data if migrating from raw SQL

### 5. Channel Management Commands

**Current state:**

- Channels configured via environment variables (`TELEGRAM_CHANNELS`, `DISCORD_CHANNEL_IDS`)
- Passed to `MessageForwarder` at initialization
- No runtime management

**Action:**

- Create database tables for channel storage:
- `discord_channels`: `(id, channel_id INTEGER UNIQUE, added_at TIMESTAMP)`
- `telegram_channels`: `(id, username TEXT UNIQUE, added_at TIMESTAMP)`
- Create new cog `src/cogs/channels.py` with commands:
- `/channels discord add <channel>` - Add Discord channel
- `/channels discord remove <channel>` - Remove Discord channel
- `/channels discord list` - List Discord channels
- `/channels telegram add <channel>` - Add Telegram channel
- `/channels telegram remove <channel>` - Remove Telegram channel
- `/channels telegram list` - List Telegram channels
- Update `MessageForwarder` to load channels from database
- Add permission checks (owner-only or allowed users)

**Files to create:**

- `src/cogs/channels.py` - Channel management commands

**Files to modify:**

- `src/shared/database.py` - Add channel table creation
- `src/services/telegram/forwarder.py` - Load channels from database
- `main.py` - Update forwarder initialization

### 6. Remove Shared Config Object

**Current state:**

- Global `config` object in `src/config.py` (line 68)
- Used in `main.py` for forwarder initialization
- Exposes `get_bot()` and `get_client()` functions

**Action:**

- Remove global `config` object
- Move environment variable loading to `initialize()` function
- Pass required values directly to services
- Keep only `get_bot()` and `get_client()` as public API
- Update `main.py` to get channel lists from database instead of config

**Files to modify:**

- `src/config.py` - Remove `Config` dataclass and global `config`, keep only getters and `initialize()`
- `main.py` - Update to load channels from database instead of config
- `src/services/telegram/forwarder.py` - Update initialization if needed

### 7. Advanced Dev Environment Setup

**Current state:**

- Basic `pyproject.toml` with ruff linting rules
- `requirements.txt` for dependencies

**Action:**

- Configure `pyproject.toml` with:
- Project metadata (name, version, description)
- `[tool.uv]` configuration for dependency management
- `[tool.ruff]` - Expand linting rules, add formatting
- `[tool.ty]` - Type checking configuration for `ty` (Astral's type checker)
- `[build-system]` - Use `hatchling` or `setuptools`
- Replace `requirements.txt` with `pyproject.toml` dependencies (or keep both for compatibility)
- Add development dependencies (ruff, ty, pytest if needed)
- Configure VS Code settings if needed

**Files to modify:**

- `pyproject.toml` - Full project configuration
- `.vscode/settings.json` - Add Python/linting settings if needed

### 7a. Development-Only Features

**Current state:**

- Log level hardcoded to `INFO` in `main.py` (line 14)
- Cog hot-reload hardcoded to `True` in `bot.py` (line 89)
- Hot-reload log message was removed in latest commit (already aligns with dev-only approach)

**Action:**

- Add environment variable `ENVIRONMENT` or `DEV_MODE` to detect development mode
- Make log level conditional:
- Development: `INFO` level (detailed logging)
- Production: `WARNING` or `ERROR` level (minimal logging)
- Make cog hot-reload conditional:
- Development: `hot_reload=True` (enable file watching)
- Production: `hot_reload=False` (disable for performance)
- Use environment variable check (e.g., `ENVIRONMENT=development` or `DEV_MODE=true`)

**Files to modify:**

- `main.py` - Make log level conditional based on environment
- `src/services/discord/bot.py` - Make hot_reload conditional based on environment
- `.env.example` - Add `ENVIRONMENT` or `DEV_MODE` variable documentation

### 8. GitHub Workflow for CI/CD

**Action:**

- Create `.github/workflows/ci.yml`
- Steps:

1. Checkout code
2. Set up Python (latest stable)
3. Install uv (if using)
4. Install dependencies
5. Run ruff linting
6. Run type checker (`ty check`)
7. Run tests (if any exist)
8. Build/verify the application can start (with production settings)

**Files to create:**

- `.github/workflows/ci.yml` - CI workflow

### 9. Modernize Commands with Embeds and Views

**Current state:**

- Some commands use embeds (`/info`, `/serverinfo`)
- Some use plain text (`/reminders` commands, `/status`)
- No interactive views (buttons, select menus)

**Action:**

- Convert all command responses to use embeds where appropriate
- Add interactive views for:
- Reminder management (buttons to delete reminders)
- Channel listing (buttons to remove channels)
- Status display (refresh button)
- Use `discord.ui.View` and `discord.ui.Button` for better UX
- Ensure consistent embed styling across commands

**Files to modify:**

- `src/cogs/info.py` - Add views to status command
- `src/cogs/reminders.py` (cog name: `lembretes`) - Convert to embeds and add delete buttons
- Current commands: `/lembretes adicionar`, `/lembretes listar`, `/lembretes remover`
- `src/cogs/channels.py` - Use embeds and views for channel management
- `src/cogs/telegram.py` - Improve embed usage if needed

## Implementation Order

### Completed ✅

1. **Database refactoring** (steps 3-4) - Foundation for other features
2. **Permission system** (step 2) - Needed for channel management
3. **Channel management** (step 5) - Depends on database, migrations, and permissions
4. **Config cleanup** (step 6) - After channel management moves to DB
5. **Command cleanup** (step 1) - Can be done independently
6. **Reminders upgrade** (step 3) - After database refactoring and migrations
7. **Dev environment** (step 7) - Independent

7a. **Development-only features** (step 7a) - Should be done early, before other features

1. **CI/CD** (step 8) - After dev environment

### Next Steps (Reordered)

1. **SQLAlchemy migration** (step 4b) - **NEXT PRIORITY**

- Migrate from raw SQL to SQLAlchemy ORM
- Support both SQLite and PostgreSQL via DATABASE_URL
- Use Alembic for migrations (replaces custom migration system)
- Convert all database access to use SQLAlchemy models
- This is a major refactor affecting all database code

1. **UI modernization** (step 9) - **AFTER SQLAlchemy**

- Convert all commands to use embeds
- Add interactive views (buttons) for reminder and channel management
- Improve UX with consistent styling

### Skipped
