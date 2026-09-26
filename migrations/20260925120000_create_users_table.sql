-- +goose Up
-- +goose StatementBegin
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = now(); RETURN NEW; END; $$ LANGUAGE plpgsql;
-- +goose StatementEnd

CREATE TABLE users (
    id                  varchar(255)    PRIMARY KEY,
    email               text            NOT NULL,
    full_name           text,
    hashed_password     text            NOT NULL,
    is_active           boolean         NOT NULL DEFAULT true,
    is_superuser        boolean         NOT NULL DEFAULT false,
    created_at          timestamptz     NOT NULL DEFAULT now(),
    updated_at          timestamptz     NOT NULL DEFAULT now(),
    deleted_at          timestamptz
);

-- Email is unique among non-deleted users so a soft-deleted email can be reused.
CREATE UNIQUE INDEX users_email_unique ON users (email) WHERE deleted_at IS NULL;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- +goose Down
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
DROP TABLE users;
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
