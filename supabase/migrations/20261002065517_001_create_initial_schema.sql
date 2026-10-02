/*
# CampusResQ AI — Initial PostgreSQL Schema

## Overview
Migrates the existing MongoDB data model to Supabase PostgreSQL.
The application uses its own JWT-based auth (bcrypt + PyJWT) stored in the
`app_users` table — it does NOT use Supabase Auth (auth.users).  The backend
connects with the service-role key and enforces all RBAC in Python, so RLS
is enabled with permissive `TO anon, authenticated` policies (the security
boundary is the FastAPI layer, not Postgres RLS).

## Tables Created (9)

1. **app_users** — replaces `users` collection.  Stores identity, role,
   department, availability, buddy/SOS contacts, language, skills,
   last known location.  `password_hash` is bcrypt.
2. **incidents** — replaces `incidents` collection.  The core entity.
   Location, evidence, AI analysis, fraud analysis, media forensics,
   responder assignment, timestamps, timeline, location history, and
   routing metadata are stored as JSONB columns.
3. **notifications** — replaces `notifications` collection.  In-app
   notification rows with read/unread state.
4. **audit_logs** — replaces `audit_logs` collection.  Immutable record of
   every significant system action with before/after JSONB snapshots.
5. **teams** — replaces `teams` collection.  Primary/backup team config
   per department.  Members stored as JSONB array.
6. **push_subscriptions** — replaces `push_subscriptions` collection.
   Web Push endpoint + VAPID keys per user.
7. **announcements** — replaces `announcements` collection.  Campus-wide
   broadcast messages.
8. **system_config** — replaces `system_config` collection.  Single-row
   global settings (SOS radius, default timeout).
9. **cron_runs** — replaces `cron_runs` collection.  Idempotency table for
   scheduled webhook/cron invocations.

## Column Type Mapping (MongoDB → Postgres)
- `id` (string UUID) → `id TEXT PRIMARY KEY` (app generates UUIDs as text)
- ISO-date strings → `TIMESTAMPTZ` where the column is always a timestamp;
  kept as TEXT only where the app serialises partial/optional timestamps.
- Nested objects (location, ai_analysis, etc.) → `JSONB`
- Arrays (timeline, evidence, etc.) → `JSONB` (default `'[]'::jsonb`)
- Enums stored as TEXT with CHECK constraints

## Security
- RLS enabled on every table.
- Policies use `TO anon, authenticated` with `USING (true)` / `WITH CHECK (true)`
  because the FastAPI backend is the security boundary — it validates JWTs,
  checks roles, and filters rows in Python before returning them to the
  client.  The service-role connection string bypasses RLS entirely, so these
  permissive policies only affect direct-anon-key access (which the app does
  not use; the frontend goes through the FastAPI backend).

## Notes
- `app_users` is named with the `app_` prefix to avoid a system table name
  clash.
- All `id` columns are TEXT (not uuid) because the Python backend generates
  UUIDs as strings via `str(uuid.uuid4())` and the frontend references them
  as strings.
- Foreign keys are not enforced between `app_users.id` and other tables'
  `reporter_id` / `assigned_responder_id` / `user_id` columns because the
  app generates IDs before insert and some flows (seed data, cron) insert
  with pre-generated IDs.  Indexes are added on these columns instead.
*/

-- ============================================================
-- 1. app_users
-- ============================================================
CREATE TABLE IF NOT EXISTS app_users (
    id                  TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    email               TEXT UNIQUE NOT NULL,
    password_hash       TEXT NOT NULL,
    role                TEXT NOT NULL DEFAULT 'student'
                        CHECK (role IN ('student','faculty','responder','dept_personnel','dept_admin','head_admin')),
    department          TEXT CHECK (department IS NULL OR department IN
                        ('medical','fire_safety','security','electrical','construction','facilities','environmental','transport')),
    phone               TEXT,
    registration_number TEXT,
    available           BOOLEAN NOT NULL DEFAULT TRUE,
    buddy_name          TEXT,
    buddy_email         TEXT,
    buddy_phone         TEXT,
    language            TEXT DEFAULT 'en',
    skills              JSONB DEFAULT '[]'::jsonb,
    last_location       JSONB,
    role_title          TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_app_users_registration_number
    ON app_users (registration_number)
    WHERE registration_number IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_app_users_role ON app_users (role);
CREATE INDEX IF NOT EXISTS idx_app_users_department ON app_users (department);

ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "app_users_all_crud" ON app_users;
CREATE POLICY "app_users_all_crud" ON app_users
    FOR ALL TO anon, authenticated
    USING (true) WITH CHECK (true);

-- ============================================================
-- 2. incidents
-- ============================================================
CREATE TABLE IF NOT EXISTS incidents (
    id                        TEXT PRIMARY KEY,
    reporter_id               TEXT NOT NULL,
    reporter_name             TEXT NOT NULL,
    description               TEXT NOT NULL,
    location                  JSONB NOT NULL,
    category_hint             TEXT,
    is_sos                    BOOLEAN NOT NULL DEFAULT FALSE,
    evidence                  JSONB DEFAULT '[]'::jsonb,
    status                    TEXT NOT NULL DEFAULT 'submitted'
                              CHECK (status IN
                              ('submitted','analyzing','classified','fraud_review','assigning',
                               'waiting_for_acceptance','assigned','accepted','en_route','arrived',
                               'resolved','resolution_pending','reopened','cancelled','escalated')),
    ai_analysis               JSONB,
    ai_analysis_localized     JSONB,
    fraud_analysis            JSONB,
    media_forensics           JSONB,
    assigned_department       TEXT CHECK (assigned_department IS NULL OR assigned_department IN
                              ('medical','fire_safety','security','electrical','construction','facilities','environmental','transport')),
    assigned_responder_id     TEXT,
    assigned_responder_name   TEXT,
    responder_location        JSONB,
    eta_minutes               INTEGER,
    priority                  TEXT CHECK (priority IS NULL OR priority IN ('low','medium','high','critical')),
    reported_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    classified_at             TIMESTAMPTZ,
    assigned_at               TIMESTAMPTZ,
    accepted_at               TIMESTAMPTZ,
    en_route_at               TIMESTAMPTZ,
    arrived_at                TIMESTAMPTZ,
    resolved_at               TIMESTAMPTZ,
    reopened_at               TIMESTAMPTZ,
    escalated                 BOOLEAN NOT NULL DEFAULT FALSE,
    client_op_id              TEXT,
    timeline                  JSONB DEFAULT '[]'::jsonb,
    reporter_confirmed_safe   BOOLEAN NOT NULL DEFAULT FALSE,
    reporter_safe_at          TIMESTAMPTZ,
    responder_marked_complete BOOLEAN NOT NULL DEFAULT FALSE,
    responder_complete_at     TIMESTAMPTZ,
    sos_broadcast_ids         JSONB DEFAULT '[]'::jsonb,
    sos_radius_m              INTEGER,
    distance_km               DOUBLE PRECISION,
    location_history          JSONB DEFAULT '[]'::jsonb,
    voice_transcript          TEXT,
    routing_status            TEXT,
    notified_at               TIMESTAMPTZ,
    assigned_team_name        TEXT,
    analysis_source           TEXT,
    availability_state        TEXT,
    available_member_count    INTEGER DEFAULT 0,
    accepted_by_department    TEXT,
    wellness_checked          BOOLEAN DEFAULT FALSE,
    wellness_checked_at       TIMESTAMPTZ,
    wellness_reply            JSONB
);

CREATE INDEX IF NOT EXISTS idx_incidents_reporter_id ON incidents (reporter_id);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents (status);
CREATE INDEX IF NOT EXISTS idx_incidents_assigned_department ON incidents (assigned_department);
CREATE INDEX IF NOT EXISTS idx_incidents_assigned_responder_id ON incidents (assigned_responder_id);
CREATE INDEX IF NOT EXISTS idx_incidents_priority ON incidents (priority);
CREATE INDEX IF NOT EXISTS idx_incidents_reported_at ON incidents (reported_at DESC);
CREATE INDEX IF NOT EXISTS idx_incidents_client_op_id ON incidents (client_op_id);
CREATE INDEX IF NOT EXISTS idx_incidents_resolved_at ON incidents (resolved_at);

ALTER TABLE incidents ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "incidents_all_crud" ON incidents;
CREATE POLICY "incidents_all_crud" ON incidents
    FOR ALL TO anon, authenticated
    USING (true) WITH CHECK (true);

-- ============================================================
-- 3. notifications
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL,
    type        TEXT NOT NULL,
    message     TEXT NOT NULL,
    incident_id TEXT,
    priority    TEXT NOT NULL DEFAULT 'medium'
                CHECK (priority IN ('low','medium','high','critical')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    read_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications (user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications (created_at DESC);

ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "notifications_all_crud" ON notifications;
CREATE POLICY "notifications_all_crud" ON notifications
    FOR ALL TO anon, authenticated
    USING (true) WITH CHECK (true);

-- ============================================================
-- 4. audit_logs
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id          TEXT PRIMARY KEY,
    actor_id    TEXT NOT NULL,
    actor_name  TEXT NOT NULL,
    actor_role  TEXT NOT NULL,
    action      TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id   TEXT NOT NULL,
    prev_value  JSONB,
    new_value   JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_id ON audit_logs (entity_id);

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "audit_logs_all_crud" ON audit_logs;
CREATE POLICY "audit_logs_all_crud" ON audit_logs
    FOR ALL TO anon, authenticated
    USING (true) WITH CHECK (true);

-- ============================================================
-- 5. teams
-- ============================================================
CREATE TABLE IF NOT EXISTS teams (
    id                    TEXT PRIMARY KEY,
    department            TEXT NOT NULL
                          CHECK (department IN
                          ('medical','fire_safety','security','electrical','construction','facilities','environmental','transport')),
    kind                  TEXT NOT NULL DEFAULT 'primary'
                          CHECK (kind IN ('primary','backup')),
    name                  TEXT NOT NULL,
    members               JSONB DEFAULT '[]'::jsonb,
    acceptance_timeout_sec INTEGER NOT NULL DEFAULT 60,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_teams_department_kind
    ON teams (department, kind);

ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "teams_all_crud" ON teams;
CREATE POLICY "teams_all_crud" ON teams
    FOR ALL TO anon, authenticated
    USING (true) WITH CHECK (true);

-- ============================================================
-- 6. push_subscriptions
-- ============================================================
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id     TEXT NOT NULL,
    endpoint    TEXT NOT NULL,
    keys        JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_push_subscriptions_endpoint
    ON push_subscriptions (endpoint);

CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user_id ON push_subscriptions (user_id);

ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "push_subscriptions_all_crud" ON push_subscriptions;
CREATE POLICY "push_subscriptions_all_crud" ON push_subscriptions
    FOR ALL TO anon, authenticated
    USING (true) WITH CHECK (true);

-- ============================================================
-- 7. announcements
-- ============================================================
CREATE TABLE IF NOT EXISTS announcements (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    body        TEXT NOT NULL,
    priority    TEXT NOT NULL DEFAULT 'high'
                CHECK (priority IN ('low','medium','high','critical')),
    author_id   TEXT NOT NULL,
    author_name TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_announcements_created_at ON announcements (created_at DESC);

ALTER TABLE announcements ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "announcements_all_crud" ON announcements;
CREATE POLICY "announcements_all_crud" ON announcements
    FOR ALL TO anon, authenticated
    USING (true) WITH CHECK (true);

-- ============================================================
-- 8. system_config
-- ============================================================
CREATE TABLE IF NOT EXISTS system_config (
    id                          TEXT PRIMARY KEY DEFAULT 'global',
    sos_radius_m                INTEGER NOT NULL DEFAULT 2000,
    default_acceptance_timeout_sec INTEGER NOT NULL DEFAULT 60
);

INSERT INTO system_config (id, sos_radius_m, default_acceptance_timeout_sec)
VALUES ('global', 2000, 60)
ON CONFLICT (id) DO NOTHING;

ALTER TABLE system_config ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "system_config_all_crud" ON system_config;
CREATE POLICY "system_config_all_crud" ON system_config
    FOR ALL TO anon, authenticated
    USING (true) WITH CHECK (true);

-- ============================================================
-- 9. cron_runs
-- ============================================================
CREATE TABLE IF NOT EXISTS cron_runs (
    id          TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    run_id      TEXT UNIQUE NOT NULL,
    at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    kind        TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_cron_runs_run_id ON cron_runs (run_id);

ALTER TABLE cron_runs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "cron_runs_all_crud" ON cron_runs;
CREATE POLICY "cron_runs_all_crud" ON cron_runs
    FOR ALL TO anon, authenticated
    USING (true) WITH CHECK (true);
