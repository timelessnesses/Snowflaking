CREATE TABLE IF NOT EXISTS new_year_config(
    guild_id BIGINT NOT NULL PRIMARY KEY,
    annouce_channel_id BIGINT,
    timezone VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS new_year_reminder_message(
    id BIGINT NOT NULL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT
);

CREATE TABLE IF NOT EXISTS new_year_message(
    id BIGINT, -- this is optional cus of uhhh we also store how message format is and stuff and yeah plus this is just for deleting purposes
    guild_id BIGINT NOT NULL PRIMARY KEY,
    channel_id BIGINT NOT NULL,
    message_format TEXT,
    ping_role_id BIGINT,
    body_message_format TEXT
);

CREATE TABLE IF NOT EXISTS christmas_config(
    guild_id BIGINT NOT NULL PRIMARY KEY,
    annouce_channel_id BIGINT,
    timezone VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS christmas_reminder_message(
    id BIGINT NOT NULL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT
);

CREATE TABLE IF NOT EXISTS christmas_message(
    id BIGINT, -- this is optional cus of uhhh we also store how message format is and stuff and yeah plus this is just for deleting purposes
    guild_id BIGINT NOT NULL PRIMARY KEY,
    channel_id BIGINT NOT NULL,
    message_format TEXT,
    ping_role_id BIGINT,
    body_message_format TEXT
);

CREATE TABLE
  IF NOT EXISTS level_user(
    user_id BIGINT NOT NULL,
    experience INTEGER NOT NULL DEFAULT 0,
    guild_id BIGINT NOT NULL DEFAULT 0
  );

CREATE TABLE
  IF NOT EXISTS guild(guild_id BIGINT);

CREATE TABLE
  IF NOT EXISTS roles_level(
    guild_id BIGINT,
    role_id BIGINT NOT NULL DEFAULT 0,
    level_ INTEGER NOT NULL DEFAULT 0
  );

CREATE TABLE
  IF NOT EXISTS levels_background(guild_id BIGINT, background TEXT DEFAULT NULL);

CREATE TABLE
  IF NOT EXISTS font_colors(guild_id BIGINT, color TEXT DEFAULT '255,255,255');

CREATE TABLE
  IF NOT EXISTS user_config(
    user_id BIGINT NOT NULL,
    send_level_up_message BOOLEAN NOT NULL DEFAULT TRUE
  );

CREATE TABLE
  IF NOT EXISTS prevent_channel_send(guild_id BIGINT NOT NULL, channel_id BIGINT NOT NULL);