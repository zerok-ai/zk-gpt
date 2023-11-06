CREATE TABLE IF NOT EXISTS public.issue_incident_inference
(
    id                      SERIAL PRIMARY KEY,
    issue_id                VARCHAR(255) NOT NULL,
    incident_id             VARCHAR(255) NOT NULL,
    issue_title             VARCHAR(255),
    scenario_id             VARCHAR(255),
    inference               BYTEA,
    created_at              TIMESTAMP,
    issue_last_seen         TIMESTAMP,
    issue_first_seen        TIMESTAMP,
    CONSTRAINT unique_issue_incident_inference UNIQUE (issue_id, incident_id)
);

CREATE TABLE IF NOT EXISTS public.issue_user_conversation_events
(
    id                      SERIAL PRIMARY KEY,
    issue_id                VARCHAR(255) NOT NULL,
    incident_id             VARCHAR(255) NOT NULL,
    event_type              VARCHAR(255) NOT NULL,
    event_request           BYTEA,
    event_response          BYTEA,
    created_at              TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.issue_incident_context
(
    id                      SERIAL PRIMARY KEY,
    issue_id                VARCHAR(255) NOT NULL,
    incident_id             VARCHAR(255) NOT NULL,
    context                 BYTEA,
    created_at              TIMESTAMP,
    updated_at              TIMESTAMP,
    CONSTRAINT unique_issue_incident_context UNIQUE (issue_id, incident_id)
);

CREATE TABLE IF NOT EXISTS public.slack_inference_report (
    id                      SERIAL PRIMARY KEY,
    issue_id                VARCHAR(255) NOT NULL,
    incident_id             VARCHAR(255) NOT NULL,
    reporting_status        BOOLEAN,
    issue_timestamp         TIMESTAMP,
    report_timestamp        TIMESTAMP,
    created_at				TIMESTAMP,
    clear_reporting_timestamp TIMESTAMP,
    CONSTRAINT unique_slack_incident_context UNIQUE (issue_id, incident_id)
);
