CREATE TABLE userSettings(
    `id` INT PRIMARY KEY NOT NULL auto_increment,
    `uid` BIGINT NOT NULL,
    `hudOverride` INT NOT NULL DEFAULT 1
)