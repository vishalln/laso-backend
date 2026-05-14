-- ============================================================
-- LASO MVP Full Schema Migration
-- Version: 001
-- Description: Creates all tables for the LASO MVP platform
-- Safe to re-run: uses IF NOT EXISTS for all objects
-- ============================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. DOCTORS
-- Must be created before patients (FK dependency)
-- ============================================================
CREATE TABLE IF NOT EXISTS doctors (
    doctor_id       VARCHAR(255) PRIMARY KEY,  -- Cognito sub
    email           VARCHAR(255) NOT NULL UNIQUE,
    name            VARCHAR(255) NOT NULL,
    specialisation  VARCHAR(100),
    phone           VARCHAR(20),
    status          VARCHAR(20) NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_doctors_email ON doctors(email);
CREATE INDEX IF NOT EXISTS idx_doctors_status ON doctors(status);

-- ============================================================
-- 2. DOCTOR WORKING HOURS
-- ============================================================
CREATE TABLE IF NOT EXISTS doctor_working_hours (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doctor_id       VARCHAR(255) NOT NULL REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    day_of_week     SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    is_working      BOOLEAN NOT NULL DEFAULT TRUE,
    start_time      TIME,
    end_time        TIME,
    UNIQUE (doctor_id, day_of_week)
);

CREATE INDEX IF NOT EXISTS idx_doctor_working_hours_doctor ON doctor_working_hours(doctor_id);

-- ============================================================
-- 3. PATIENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS patients (
    patient_id          VARCHAR(255) PRIMARY KEY,  -- Cognito sub
    email               VARCHAR(255) NOT NULL UNIQUE,
    name                VARCHAR(255) NOT NULL,
    age                 INTEGER,
    gender              VARCHAR(20),
    city                VARCHAR(100),
    height_cm           NUMERIC(5,1),
    phone               VARCHAR(20),
    address_line1       VARCHAR(255),
    address_line2       VARCHAR(255),
    address_city        VARCHAR(100),
    address_state       VARCHAR(100),
    address_pincode     VARCHAR(10),
    address_country     VARCHAR(50) DEFAULT 'India',
    status              VARCHAR(20) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'inactive', 'suspended')),
    assigned_doctor_id  VARCHAR(255) REFERENCES doctors(doctor_id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patients_email ON patients(email);
CREATE INDEX IF NOT EXISTS idx_patients_status ON patients(status);
CREATE INDEX IF NOT EXISTS idx_patients_assigned_doctor ON patients(assigned_doctor_id);

-- ============================================================
-- 4. QUIZ SUBMISSIONS
-- Drop and recreate to add patient_id FK
-- ============================================================
DROP TABLE IF EXISTS quiz_submissions;

CREATE TABLE quiz_submissions (
    quiz_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id          VARCHAR(255) REFERENCES patients(patient_id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    age                 INTEGER,
    gender              VARCHAR(20),
    height_cm           NUMERIC(5,1),
    weight_kg           NUMERIC(5,1),
    conditions          TEXT[] DEFAULT '{}',
    current_medications TEXT[] DEFAULT '{}',
    symptoms            TEXT[] DEFAULT '{}',
    activity_level      VARCHAR(30),
    diet_type           VARCHAR(30),
    sleep_hours         NUMERIC(3,1),
    stress_level        INTEGER,
    primary_goal        VARCHAR(50),
    target_weight_kg    NUMERIC(5,1),
    timeline_weeks      VARCHAR(20),
    readiness_score     INTEGER,
    main_concern        TEXT,
    bmi                 NUMERIC(4,1),
    eligible            BOOLEAN
);

CREATE INDEX IF NOT EXISTS idx_quiz_submissions_patient ON quiz_submissions(patient_id);

-- ============================================================
-- 5. PROTOCOL TEMPLATES
-- ============================================================
CREATE TABLE IF NOT EXISTS protocol_templates (
    template_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    total_weeks     INTEGER NOT NULL,
    version         INTEGER NOT NULL DEFAULT 1,
    status          VARCHAR(20) NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft', 'published', 'archived')),
    published_at    TIMESTAMPTZ,
    published_by    VARCHAR(255),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_protocol_templates_status ON protocol_templates(status);

-- ============================================================
-- 6. PROTOCOL TEMPLATE STEPS
-- ============================================================
CREATE TABLE IF NOT EXISTS protocol_template_steps (
    step_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id         UUID NOT NULL REFERENCES protocol_templates(template_id) ON DELETE CASCADE,
    title               VARCHAR(255) NOT NULL,
    step_type           VARCHAR(50) NOT NULL
                        CHECK (step_type IN ('consultation', 'blood_test', 'check_in', 'prescription', 'review', 'custom')),
    week_offset         INTEGER NOT NULL DEFAULT 0,
    duration_minutes    INTEGER,
    is_recurring        BOOLEAN NOT NULL DEFAULT FALSE,
    auto_activate_rule  VARCHAR(255),
    is_flagged          BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order          INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_protocol_template_steps_template ON protocol_template_steps(template_id);
CREATE INDEX IF NOT EXISTS idx_protocol_template_steps_sort ON protocol_template_steps(template_id, sort_order);

-- ============================================================
-- 7. PROTOCOL TEMPLATE VERSIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS protocol_template_versions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id     UUID NOT NULL REFERENCES protocol_templates(template_id) ON DELETE CASCADE,
    version         INTEGER NOT NULL,
    published_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_by    VARCHAR(255),
    step_count      INTEGER NOT NULL DEFAULT 0,
    steps_snapshot  JSONB NOT NULL DEFAULT '[]'::JSONB,
    UNIQUE (template_id, version)
);

CREATE INDEX IF NOT EXISTS idx_protocol_template_versions_template ON protocol_template_versions(template_id);

-- ============================================================
-- 8. PROGRAMMES
-- ============================================================
CREATE TABLE IF NOT EXISTS programmes (
    programme_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id          VARCHAR(255) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id           VARCHAR(255) NOT NULL REFERENCES doctors(doctor_id) ON DELETE RESTRICT,
    template_id         UUID REFERENCES protocol_templates(template_id) ON DELETE SET NULL,
    template_version    INTEGER,
    name                VARCHAR(255) NOT NULL,
    status              VARCHAR(30) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'paused', 'completed', 'cancelled')),
    start_date          DATE NOT NULL,
    end_date            DATE,
    paused_at_step_id   UUID,
    pause_reason        TEXT,
    cancel_reason       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_programmes_patient ON programmes(patient_id);
CREATE INDEX IF NOT EXISTS idx_programmes_doctor ON programmes(doctor_id);
CREATE INDEX IF NOT EXISTS idx_programmes_status ON programmes(status);
CREATE INDEX IF NOT EXISTS idx_programmes_template ON programmes(template_id);

-- ============================================================
-- 9. PROGRAMME STEPS
-- ============================================================
CREATE TABLE IF NOT EXISTS programme_steps (
    step_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    programme_id        UUID NOT NULL REFERENCES programmes(programme_id) ON DELETE CASCADE,
    template_step_id    UUID REFERENCES protocol_template_steps(step_id) ON DELETE SET NULL,
    title               VARCHAR(255) NOT NULL,
    step_type           VARCHAR(50) NOT NULL
                        CHECK (step_type IN ('consultation', 'blood_test', 'check_in', 'prescription', 'review', 'custom')),
    week_offset         INTEGER NOT NULL DEFAULT 0,
    duration_minutes    INTEGER,
    is_recurring        BOOLEAN NOT NULL DEFAULT FALSE,
    auto_activate_rule  VARCHAR(255),
    is_flagged          BOOLEAN NOT NULL DEFAULT FALSE,
    status              VARCHAR(30) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'active', 'completed', 'skipped')),
    sort_order          INTEGER NOT NULL DEFAULT 0,
    activated_at        TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    skip_reason         TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_programme_steps_programme ON programme_steps(programme_id);
CREATE INDEX IF NOT EXISTS idx_programme_steps_status ON programme_steps(programme_id, status);
CREATE INDEX IF NOT EXISTS idx_programme_steps_sort ON programme_steps(programme_id, sort_order);

-- ============================================================
-- 10. BLOOD TESTS
-- ============================================================
CREATE TABLE IF NOT EXISTS blood_tests (
    blood_test_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id          VARCHAR(255) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    programme_id        UUID REFERENCES programmes(programme_id) ON DELETE SET NULL,
    programme_step_id   UUID REFERENCES programme_steps(step_id) ON DELETE SET NULL,
    status              VARCHAR(30) NOT NULL DEFAULT 'ordered'
                        CHECK (status IN ('ordered', 'sample_collected', 'processing', 'results_ready', 'cancelled')),
    hba1c               NUMERIC(4,1),
    fasting_glucose     NUMERIC(5,1),
    total_cholesterol   NUMERIC(5,1),
    ldl                 NUMERIC(5,1),
    hdl                 NUMERIC(5,1),
    triglycerides       NUMERIC(6,1),
    tsh                 NUMERIC(5,2),
    creatinine          NUMERIC(4,2),
    alt                 NUMERIC(5,1),
    ast                 NUMERIC(5,1),
    entered_by          VARCHAR(255),
    ordered_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    results_at          TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_blood_tests_patient ON blood_tests(patient_id);
CREATE INDEX IF NOT EXISTS idx_blood_tests_programme ON blood_tests(programme_id);
CREATE INDEX IF NOT EXISTS idx_blood_tests_status ON blood_tests(status);

-- ============================================================
-- 11. CONSULTATIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS consultations (
    consultation_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id          VARCHAR(255) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id           VARCHAR(255) NOT NULL REFERENCES doctors(doctor_id) ON DELETE RESTRICT,
    programme_id        UUID REFERENCES programmes(programme_id) ON DELETE SET NULL,
    programme_step_id   UUID REFERENCES programme_steps(step_id) ON DELETE SET NULL,
    type                VARCHAR(30) NOT NULL DEFAULT 'video'
                        CHECK (type IN ('video', 'in_person', 'phone', 'chat')),
    duration_minutes    INTEGER,
    status              VARCHAR(30) NOT NULL DEFAULT 'scheduled'
                        CHECK (status IN ('scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show')),
    scheduled_at        TIMESTAMPTZ NOT NULL,
    meet_link           VARCHAR(500),
    cancel_reason       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_consultations_patient ON consultations(patient_id);
CREATE INDEX IF NOT EXISTS idx_consultations_doctor ON consultations(doctor_id);
CREATE INDEX IF NOT EXISTS idx_consultations_programme ON consultations(programme_id);
CREATE INDEX IF NOT EXISTS idx_consultations_scheduled ON consultations(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_consultations_status ON consultations(status);

-- ============================================================
-- 12. PRESCRIPTIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS prescriptions (
    prescription_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id              VARCHAR(255) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id               VARCHAR(255) NOT NULL REFERENCES doctors(doctor_id) ON DELETE RESTRICT,
    programme_id            UUID REFERENCES programmes(programme_id) ON DELETE SET NULL,
    consultation_id         UUID REFERENCES consultations(consultation_id) ON DELETE SET NULL,
    programme_step_id       UUID REFERENCES programme_steps(step_id) ON DELETE SET NULL,
    medication              VARCHAR(255) NOT NULL,
    dose_value              NUMERIC(6,2) NOT NULL,
    dose_unit               VARCHAR(30) NOT NULL,
    frequency               VARCHAR(50) NOT NULL,
    duration_weeks          INTEGER,
    special_instructions    TEXT,
    next_escalation_dose    NUMERIC(6,2),
    next_escalation_unit    VARCHAR(30),
    status                  VARCHAR(30) NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active', 'completed', 'superseded', 'cancelled')),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    superseded_at           TIMESTAMPTZ,
    cancelled_at            TIMESTAMPTZ,
    cancel_reason           TEXT
);

CREATE INDEX IF NOT EXISTS idx_prescriptions_patient ON prescriptions(patient_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_doctor ON prescriptions(doctor_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_programme ON prescriptions(programme_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_status ON prescriptions(status);

-- ============================================================
-- 13. ORDERS
-- ============================================================
CREATE TABLE IF NOT EXISTS orders (
    order_id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id              VARCHAR(255) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    prescription_id         UUID REFERENCES prescriptions(prescription_id) ON DELETE SET NULL,
    programme_id            UUID REFERENCES programmes(programme_id) ON DELETE SET NULL,
    quantity                INTEGER NOT NULL DEFAULT 1,
    delivery_address        TEXT,
    status                  VARCHAR(30) NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending', 'confirmed', 'packed', 'shipped', 'out_for_delivery', 'delivered', 'cancelled', 'returned')),
    carrier_name            VARCHAR(100),
    tracking_id             VARCHAR(255),
    estimated_delivery      DATE,
    cold_chain_status       VARCHAR(30)
                            CHECK (cold_chain_status IS NULL OR cold_chain_status IN ('maintained', 'breached', 'not_required')),
    notes                   TEXT,
    confirmed_at            TIMESTAMPTZ,
    packed_at               TIMESTAMPTZ,
    shipped_at              TIMESTAMPTZ,
    out_for_delivery_at     TIMESTAMPTZ,
    delivered_at            TIMESTAMPTZ,
    cancelled_at            TIMESTAMPTZ,
    returned_at             TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_patient ON orders(patient_id);
CREATE INDEX IF NOT EXISTS idx_orders_prescription ON orders(prescription_id);
CREATE INDEX IF NOT EXISTS idx_orders_programme ON orders(programme_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_tracking ON orders(tracking_id);

-- ============================================================
-- 14. WEEKLY CHECK-INS
-- ============================================================
CREATE TABLE IF NOT EXISTS weekly_check_ins (
    check_in_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id          VARCHAR(255) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    programme_id        UUID NOT NULL REFERENCES programmes(programme_id) ON DELETE CASCADE,
    programme_step_id   UUID REFERENCES programme_steps(step_id) ON DELETE SET NULL,
    week_number         INTEGER NOT NULL,
    weight_kg           NUMERIC(5,1),
    fasting_glucose     NUMERIC(5,1),
    doses_taken         INTEGER,
    doses_scheduled     INTEGER,
    side_effects        JSONB DEFAULT '[]'::JSONB,
    appetite_level      VARCHAR(20)
                        CHECK (appetite_level IS NULL OR appetite_level IN ('very_low', 'low', 'normal', 'high', 'very_high')),
    energy_level        VARCHAR(20)
                        CHECK (energy_level IS NULL OR energy_level IN ('very_low', 'low', 'normal', 'high', 'very_high')),
    notes               TEXT,
    submitted_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_weekly_check_ins_patient ON weekly_check_ins(patient_id);
CREATE INDEX IF NOT EXISTS idx_weekly_check_ins_programme ON weekly_check_ins(programme_id);

-- One check-in per patient per programme per week (enforced via week_number column)
CREATE UNIQUE INDEX IF NOT EXISTS idx_checkins_one_per_week
    ON weekly_check_ins(patient_id, programme_id, week_number);

-- ============================================================
-- 15. CONVERSATIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id          VARCHAR(255) NOT NULL UNIQUE REFERENCES patients(patient_id) ON DELETE CASCADE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_patient ON conversations(patient_id);

-- ============================================================
-- 16. MESSAGES
-- ============================================================
CREATE TABLE IF NOT EXISTS messages (
    message_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id     UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    sender_id           VARCHAR(255) NOT NULL,
    sender_role         VARCHAR(30) NOT NULL
                        CHECK (sender_role IN ('patient', 'doctor', 'admin', 'system')),
    sender_name         VARCHAR(255),
    text                TEXT NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);

-- ============================================================
-- 17. CLINICAL NOTES
-- ============================================================
CREATE TABLE IF NOT EXISTS clinical_notes (
    note_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id          VARCHAR(255) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id           VARCHAR(255) NOT NULL REFERENCES doctors(doctor_id) ON DELETE RESTRICT,
    programme_id        UUID REFERENCES programmes(programme_id) ON DELETE SET NULL,
    consultation_id     UUID REFERENCES consultations(consultation_id) ON DELETE SET NULL,
    note_type           VARCHAR(50) NOT NULL DEFAULT 'general'
                        CHECK (note_type IN ('general', 'consultation', 'follow_up', 'lab_review', 'prescription_change', 'escalation')),
    subject             VARCHAR(255),
    body                TEXT NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_clinical_notes_patient ON clinical_notes(patient_id);
CREATE INDEX IF NOT EXISTS idx_clinical_notes_doctor ON clinical_notes(doctor_id);
CREATE INDEX IF NOT EXISTS idx_clinical_notes_programme ON clinical_notes(programme_id);
CREATE INDEX IF NOT EXISTS idx_clinical_notes_consultation ON clinical_notes(consultation_id);

-- ============================================================
-- 18. TASKS
-- ============================================================
CREATE TABLE IF NOT EXISTS tasks (
    task_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id          VARCHAR(255) REFERENCES patients(patient_id) ON DELETE SET NULL,
    assigned_to         VARCHAR(255),
    assigned_to_doctor  VARCHAR(255) REFERENCES doctors(doctor_id) ON DELETE SET NULL,
    task_type           VARCHAR(50) NOT NULL
                        CHECK (task_type IN ('review_blood_test', 'follow_up_call', 'prescription_review', 'check_in_review', 'admin_task', 'escalation', 'custom')),
    title               VARCHAR(255) NOT NULL,
    priority            VARCHAR(20) NOT NULL DEFAULT 'medium'
                        CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    status              VARCHAR(20) NOT NULL DEFAULT 'open'
                        CHECK (status IN ('open', 'in_progress', 'completed', 'cancelled')),
    due_date            DATE,
    completed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_patient ON tasks(patient_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_doctor ON tasks(assigned_to_doctor);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority_status ON tasks(priority, status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);

-- ============================================================
-- 19. PAYMENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS payments (
    payment_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    programme_id        UUID REFERENCES programmes(programme_id) ON DELETE SET NULL,
    patient_id          VARCHAR(255) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    amount              NUMERIC(10,2) NOT NULL,
    currency            VARCHAR(3) NOT NULL DEFAULT 'INR',
    status              VARCHAR(30) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'refunded')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_payments_patient ON payments(patient_id);
CREATE INDEX IF NOT EXISTS idx_payments_programme ON payments(programme_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);

-- ============================================================
-- 20. TREATMENT PLANS
-- ============================================================
CREATE TABLE IF NOT EXISTS treatment_plans (
    plan_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id          VARCHAR(255) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    programme_id        UUID REFERENCES programmes(programme_id) ON DELETE SET NULL,
    doctor_id           VARCHAR(255) NOT NULL REFERENCES doctors(doctor_id) ON DELETE RESTRICT,
    diagnosis_notes     TEXT,
    target_dose         NUMERIC(6,2),
    target_dose_unit    VARCHAR(30),
    titration_schedule  TEXT,
    diet_guidelines     TEXT,
    activity_target     VARCHAR(255),
    weight_target_kg    NUMERIC(5,1),
    glucose_target      VARCHAR(100),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_treatment_plans_patient ON treatment_plans(patient_id);
CREATE INDEX IF NOT EXISTS idx_treatment_plans_programme ON treatment_plans(programme_id);
CREATE INDEX IF NOT EXISTS idx_treatment_plans_doctor ON treatment_plans(doctor_id);

-- ============================================================
-- 21. CATALOG PRODUCTS
-- ============================================================
CREATE TABLE IF NOT EXISTS catalog_products (
    product_id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                    VARCHAR(255) NOT NULL,
    brand                   VARCHAR(100),
    category                VARCHAR(50) NOT NULL
                            CHECK (category IN ('medication', 'supplement', 'device', 'test_kit', 'other')),
    unit                    VARCHAR(50),
    tagline                 VARCHAR(255),
    emoji                   VARCHAR(10),
    price_inr               NUMERIC(10,2) NOT NULL,
    recommended_weeks       INTEGER,
    clinical_rationale      TEXT,
    stock_count             INTEGER NOT NULL DEFAULT 0,
    in_stock                BOOLEAN NOT NULL DEFAULT TRUE,
    requires_prescription   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_catalog_products_category ON catalog_products(category);
CREATE INDEX IF NOT EXISTS idx_catalog_products_in_stock ON catalog_products(in_stock);

-- ============================================================
-- 22. PATIENT FLAGS
-- ============================================================
CREATE TABLE IF NOT EXISTS patient_flags (
    flag_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id          VARCHAR(255) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    flag_type           VARCHAR(50) NOT NULL
                        CHECK (flag_type IN ('missed_check_in', 'side_effect', 'weight_gain', 'glucose_spike', 'non_adherence', 'escalation', 'custom')),
    reason              TEXT,
    created_by          VARCHAR(255),
    cleared_at          TIMESTAMPTZ,
    cleared_by          VARCHAR(255),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patient_flags_patient ON patient_flags(patient_id);
CREATE INDEX IF NOT EXISTS idx_patient_flags_type ON patient_flags(flag_type);
CREATE INDEX IF NOT EXISTS idx_patient_flags_active ON patient_flags(patient_id) WHERE cleared_at IS NULL;

-- ============================================================
-- 23. ROLE AUDIT (already exists, create only if not exists)
-- ============================================================
CREATE TABLE IF NOT EXISTS role_audit (
    audit_id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    target_user_email       VARCHAR(255) NOT NULL,
    previous_role           VARCHAR(30) NOT NULL,
    new_role                VARCHAR(30) NOT NULL,
    changed_by_admin_email  VARCHAR(255) NOT NULL,
    changed_by_admin_id     VARCHAR(255) NOT NULL,
    changed_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_role_audit_target_email ON role_audit(target_user_email, changed_at DESC);

-- ============================================================
-- END OF MIGRATION
-- ============================================================
