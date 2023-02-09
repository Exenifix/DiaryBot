CREATE TABLE IF NOT EXISTS entries
(
    user_id    BIGINT        NOT NULL,
    created_at DATE          NOT NULL DEFAULT CURRENT_DATE,
    content    VARCHAR(1024) NOT NULL,
    UNIQUE (user_id, created_at)
);

CREATE TABLE IF NOT EXISTS notifications
(
    user_id           BIGINT PRIMARY KEY,
    notification_time TIME NOT NULL,
    last_notified     DATE
);

CREATE TABLE IF NOT EXISTS moods
(
    user_id BIGINT   NOT NULL,
    mood    SMALLINT NOT NULL CHECK (mood BETWEEN 1 AND 10),
    day     DATE     NOT NULL DEFAULT CURRENT_DATE,
    UNIQUE (user_id, day)
);

CREATE TABLE IF NOT EXISTS migrations
(
    id UUID PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS script_executed
(
    id              SMALLINT PRIMARY KEY,
    script_executed TIMESTAMP NOT NULL
);

INSERT INTO script_executed (id, script_executed)
VALUES (0, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;
