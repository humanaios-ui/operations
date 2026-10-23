-- Planning schema only. Production repository adapter and RLS/privileges NOT yet implemented.
-- Use a transaction and limited DB roles; do NOT apply to live databases without review.
CREATE TABLE player_accounts (player_id uuid PRIMARY KEY, created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE player_identity_links (provider text NOT NULL CHECK(provider IN ('firstparty','discord')), subject text NOT NULL,
 player_id uuid NOT NULL REFERENCES player_accounts(player_id), PRIMARY KEY(provider,subject));
CREATE INDEX idx_player_identity_reverse ON player_identity_links(player_id);
CREATE TABLE player_consent (player_id uuid NOT NULL REFERENCES player_accounts(player_id), purpose text NOT NULL CHECK(purpose IN ('WITNESS','RESEARCH')),
 enabled boolean NOT NULL, changed_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(player_id,purpose));
CREATE TABLE campaign_memory (campaign_id text PRIMARY KEY, created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE campaign_membership (campaign_id text NOT NULL REFERENCES campaign_memory(campaign_id), player_id uuid NOT NULL REFERENCES player_accounts(player_id),
 ordinal integer NOT NULL CHECK(ordinal>0), joined_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(campaign_id,player_id), UNIQUE(campaign_id,ordinal));
CREATE TABLE witness_event (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, campaign_id text NOT NULL REFERENCES campaign_memory(campaign_id),
 player_id uuid NOT NULL REFERENCES player_accounts(player_id), source_ref text NOT NULL, source_digest text NOT NULL,
 kind text NOT NULL, summary text NOT NULL, visibility text NOT NULL CHECK(visibility IN ('PRIVATE','CAMPAIGN','PUBLIC')),
 created_at timestamptz NOT NULL DEFAULT now(), previous_digest text NOT NULL, digest text NOT NULL, UNIQUE(campaign_id,source_ref));
CREATE INDEX idx_witness_event_campaign ON witness_event(campaign_id,id);
CREATE INDEX idx_witness_event_player ON witness_event(player_id,id);
CREATE TABLE human_witness_attestation (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, player_id uuid NOT NULL REFERENCES player_accounts(player_id),
 event_id bigint NOT NULL REFERENCES witness_event(id), choice text NOT NULL CHECK(choice IN ('ACKNOWLEDGE','CONTEST','DECLINE')),
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(player_id,event_id,choice));
-- Add append-only storage triggers and access roles before deployment.
