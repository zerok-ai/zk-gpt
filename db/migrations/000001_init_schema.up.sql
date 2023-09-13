CREATE TABLE IF NOT EXISTS issue_incident_conversation
(
    id                  SERIAL PRIMARY KEY,
    issue_id            VARCHAR(255),
    incident_id         VARCHAR(255),
    query               BYTEA,
    answer              BYTEA,
    created_at          TIMESTAMP,
    is_rca              BOOLEAN,
    CONSTRAINT unique_issue_incident_rca UNIQUE (issue_id, inciden_id) WHERE is_rca = true
);

CREATE TABLE IF NOT EXISTS issue_incident_context
(
    id          SERIAL PRIMARY KEY,
    issue_id    VARCHAR(255),
    incident_id VARCHAR(255),
    context     BYTEA,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_issue_id ON issue_incident_conversation(issue_id);
CREATE INDEX idx_incident_id ON issue_incident_conversation(incident_id);
