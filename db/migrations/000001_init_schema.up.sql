CREATE TABLE IF NOT EXISTS public.issue_incident_inference
(
    id                      SERIAL PRIMARY KEY,
    issue_id                VARCHAR(255) NOT NULL,
    incident_id             VARCHAR(255) NOT NULL,
    inference               BYTEA,
    created_at              TIMESTAMP,
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