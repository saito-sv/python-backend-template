-- +goose Up
CREATE TABLE posts (
    id                  varchar(255)    PRIMARY KEY,
    user_id             varchar(255)    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title               varchar(200)    NOT NULL,
    content             text            NOT NULL,
    created_at          timestamptz     NOT NULL DEFAULT now(),
    updated_at          timestamptz     NOT NULL DEFAULT now(),
    deleted_at          timestamptz
);

CREATE INDEX posts_user_id_idx ON posts (user_id);

CREATE TRIGGER update_posts_updated_at
    BEFORE UPDATE ON posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- +goose Down
DROP TRIGGER IF EXISTS update_posts_updated_at ON posts;
DROP TABLE posts;
