-- LASO PostgreSQL Schema
-- Run against RDS after LasoDataStack is deployed

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE quiz_submissions (
    quiz_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    age             INTEGER,
    gender          VARCHAR(20),
    height_cm       NUMERIC(5,1),
    weight_kg       NUMERIC(5,1),
    conditions      TEXT[] DEFAULT '{}',
    current_medications TEXT[] DEFAULT '{}',
    symptoms        TEXT[] DEFAULT '{}',
    activity_level  VARCHAR(30),
    diet_type       VARCHAR(30),
    sleep_hours     NUMERIC(3,1),
    stress_level    INTEGER,
    primary_goal    VARCHAR(50),
    target_weight_kg NUMERIC(5,1),
    timeline_weeks  VARCHAR(20),
    readiness_score INTEGER,
    main_concern    TEXT,
    bmi             NUMERIC(4,1),
    eligible        BOOLEAN
);

CREATE TABLE role_audit (
    audit_id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    target_user_email       VARCHAR(255) NOT NULL,
    previous_role           VARCHAR(30) NOT NULL,
    new_role                VARCHAR(30) NOT NULL,
    changed_by_admin_email  VARCHAR(255) NOT NULL,
    changed_by_admin_id     VARCHAR(255) NOT NULL,
    changed_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_role_audit_target_email ON role_audit (target_user_email, changed_at DESC);
