CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS work_packets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    objective TEXT,
    status TEXT NOT NULL,
    readiness_score NUMERIC,
    high_stakes BOOLEAN DEFAULT FALSE,
    cloud_policy JSONB,
    source_policy JSONB,
    output_policy JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    raw_user_request TEXT,
    structured_yaml TEXT
);

CREATE TABLE IF NOT EXISTS clarification_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_packet_id UUID REFERENCES work_packets(id),
    round_number INTEGER,
    category TEXT,
    question TEXT,
    priority INTEGER,
    blocking BOOLEAN,
    answered BOOLEAN DEFAULT FALSE,
    answer TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    answered_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS execution_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_packet_id UUID REFERENCES work_packets(id),
    temporal_workflow_id TEXT,
    status TEXT,
    mode TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_summary TEXT
);

CREATE TABLE IF NOT EXISTS model_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_run_id UUID REFERENCES execution_runs(id),
    work_packet_id UUID REFERENCES work_packets(id),
    file_path TEXT,
    task_type TEXT,
    model_group TEXT,
    actual_model TEXT,
    local_or_cloud TEXT,
    prompt_chars INTEGER,
    response_chars INTEGER,
    success BOOLEAN,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_run_id UUID REFERENCES execution_runs(id),
    work_packet_id UUID REFERENCES work_packets(id),
    file_path TEXT,
    quality_score NUMERIC,
    grounding_score NUMERIC,
    completeness_score NUMERIC,
    actionability_score NUMERIC,
    contradiction_score NUMERIC,
    hallucination_risk TEXT,
    needs_retry BOOLEAN,
    recommended_next_step TEXT,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_run_id UUID REFERENCES execution_runs(id),
    work_packet_id UUID REFERENCES work_packets(id),
    artifact_type TEXT,
    file_path TEXT,
    obsidian_path TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS memory_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_artifact_id UUID REFERENCES artifacts(id),
    candidate_text TEXT,
    destination_suggestion TEXT,
    confidence TEXT,
    memory_type TEXT,
    approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_work_packets_status ON work_packets(status);
CREATE INDEX IF NOT EXISTS idx_questions_work_packet ON clarification_questions(work_packet_id);
CREATE INDEX IF NOT EXISTS idx_execution_runs_work_packet ON execution_runs(work_packet_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_work_packet ON artifacts(work_packet_id);
